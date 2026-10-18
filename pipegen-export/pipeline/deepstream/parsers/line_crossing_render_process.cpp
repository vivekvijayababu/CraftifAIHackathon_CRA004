#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include <cmath>
#include <string>
#include <map>
#include <set>
#include <sstream>
#include <algorithm>

#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/dnn.hpp>

#include "nvcustomprocess.h"

#include <gst/gst.h>
#include "nvdsmeta.h"
#include "gstnvdsinfer.h"
#include "realsense_meta.h"
#include "render_meta.h"

static void write_nv12(const cv::Mat &bgr, NvDsCustomPostProcessFrameInCpu *in) {
    const int W = in->W, H = in->H;
    cv::Mat i420; cv::cvtColor(bgr, i420, cv::COLOR_BGR2YUV_I420);
    const uint8_t *ysrc = i420.data;
    const uint8_t *usrc = ysrc + (size_t)W * H;
    const uint8_t *vsrc = usrc + (size_t)(W / 2) * (H / 2);
    for (int r = 0; r < H; ++r)
        memcpy(in->Y_host + (size_t)r * in->Y_pitch, ysrc + (size_t)r * W, (size_t)W);
    const int cW = W / 2, cH = H / 2;
    for (int r = 0; r < cH; ++r) {
        uint8_t *dst = in->UV_host + (size_t)r * in->UV_pitch;
        const uint8_t *u = usrc + (size_t)r * cW, *v = vsrc + (size_t)r * cW;
        for (int c = 0; c < cW; ++c) { dst[2*c] = u[c]; dst[2*c+1] = v[c]; }
    }
}

static cv::Mat read_nv12_bgr(NvDsCustomPostProcessFrameInCpu *in) {
    const int W = in->W, H = in->H;
    cv::Mat yuv(H + H / 2, W, CV_8UC1);
    for (int r = 0; r < H; ++r)
        memcpy(yuv.ptr(r), in->Y_host + (size_t)r * in->Y_pitch, (size_t)W);
    for (int r = 0; r < H / 2; ++r)
        memcpy(yuv.ptr(H + r), in->UV_host + (size_t)r * in->UV_pitch, (size_t)W);
    cv::Mat bgr; cv::cvtColor(yuv, bgr, cv::COLOR_YUV2BGR_NV12); return bgr;
}

static const RsMeta *find_rs_meta(NvDsFrameMeta *fm) {
    if (!fm) return nullptr;
    static gsize t = 0;
    if (g_once_init_enter(&t)) {
        gsize v = (gsize) nvds_get_user_meta_type((gchar *) RS_NVDS_META_NAME);
        g_once_init_leave(&t, v);
    }
    for (NvDsMetaList *l = fm->frame_user_meta_list; l; l = l->next) {
        NvDsUserMeta *um = (NvDsUserMeta *) l->data;
        if (um && um->base_meta.meta_type == (NvDsMetaType) t)
            return (const RsMeta *) um->user_meta_data;
    }
    return nullptr;
}

struct TensorRef { const float *data; int d[4]; int ndim; long total; const char *name; };

static std::vector<TensorRef> collect_tensors(NvDsCustomPostProcessFrameInCpu *in) {
    std::vector<TensorRef> out;
    for (int mi = 0; mi < (int) in->num_tensor_metas; ++mi) {
        NvDsInferTensorMeta *tm = (NvDsInferTensorMeta *) in->tensor_metas[mi];
        if (!tm) continue;
        for (unsigned li = 0; li < tm->num_output_layers; ++li) {
            const float *host = (const float *) tm->out_buf_ptrs_host[li];
            if (!host) continue;
            NvDsInferLayerInfo &info = tm->output_layers_info[li];
            TensorRef t; t.data = host; t.name = info.layerName;
            int nd = (int) info.inferDims.numDims, base = 0;
            if (nd > 0 && info.inferDims.d[0] == 1) { base = 1; nd--; }
            t.ndim = nd > 4 ? 4 : nd; t.total = 1;
            for (int i = 0; i < 4; ++i) t.d[i] = 1;
            for (int i = 0; i < t.ndim; ++i) { t.d[i] = info.inferDims.d[base + i]; t.total *= t.d[i]; }
            out.push_back(t);
        }
    }
    return out;
}

static const TensorRef *find_tensor(const std::vector<TensorRef> &ts,
                                    int a, int b = -1, int c = -1, int d = -1) {
    int want = (b < 0) ? 1 : (c < 0) ? 2 : (d < 0) ? 3 : 4;
    for (const TensorRef &t : ts) {
        if (t.ndim != want || t.d[0] != a) continue;
        if (b >= 0 && t.d[1] != b) continue;
        if (c >= 0 && t.d[2] != c) continue;
        if (d >= 0 && t.d[3] != d) continue;
        return &t;
    }
    return nullptr;
}

static std::vector<int> nms_classaware(const std::vector<cv::Rect> &boxes,
        const std::vector<float> &scores, const std::vector<int> &classIds,
        float scoreThr, float iouThr) {
    std::vector<cv::Rect> off(boxes.size());
    const float STRIDE = 100000.0f;
    for (size_t i = 0; i < boxes.size(); ++i) {
        int s = (int)(classIds[i] * STRIDE);
        off[i] = cv::Rect(boxes[i].x + s, boxes[i].y + s, boxes[i].width, boxes[i].height);
    }
    std::vector<int> keep;
    cv::dnn::NMSBoxes(off, scores, scoreThr, iouThr, keep);
    return keep;
}

static void place_panel(cv::Mat &canvas, const cv::Mat &panel,
                        int r, int c, int rows, int cols) {
    int cw = canvas.cols / cols, ch = canvas.rows / rows;
    if (cw <= 0 || ch <= 0 || panel.empty()) return;
    cv::Mat dst = canvas(cv::Rect(c * cw, r * ch, cw, ch));
    cv::Mat resized; cv::resize(panel, resized, dst.size());
    resized.copyTo(dst);
}

static cv::Mat colormap_minmax(const float *data, int h, int w, int cvColormap) {
    cv::Mat f(h, w, CV_32FC1, (void *) data);
    double mn = 0, mx = 0; cv::minMaxLoc(f, &mn, &mx);
    double scale = (mx > mn) ? 255.0 / (mx - mn) : 0.0;
    cv::Mat u8; f.convertTo(u8, CV_8UC1, scale, -mn * scale);
    cv::Mat color; cv::applyColorMap(u8, color, cvColormap);
    return color;
}

// ─── Line crossing constants ────────────────────────────────────────────────
static const double LINE_AX = 640.0, LINE_AY = 100.0;
static const double LINE_BX = 640.0, LINE_BY = 620.0;
static const double LINE_VX = LINE_BX - LINE_AX;  // 0
static const double LINE_VY = LINE_BY - LINE_AY;   // 520

// COCO class ID -> label for the 6 road-user classes
static const char* CLASS_NAMES[] = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus",
    "train", "truck", "boat", "traffic light", "fire hydrant",
    "stop sign", "parking meter", "bench", "bird", "cat", "dog",
    "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
    "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat",
    "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl",
    "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
    "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop",
    "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
    "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush"
};
static const int NUM_COCO_CLASSES = 80;

// The 6 selected road-user COCO class IDs
static const int SELECTED_IDS[] = {0, 1, 2, 3, 5, 7};
static const int NUM_SELECTED = 6;
// Labels matching SELECTED_IDS order
static const char* SELECTED_LABELS[] = {"person", "bicycle", "car", "motorcycle", "bus", "truck"};

// Order for display rows
static const char* COUNT_LABELS[] = {"person", "bicycle", "car", "motorcycle", "bus", "truck"};
static const int NUM_COUNT_LABELS = 6;

static inline bool is_selected(int cid) {
    for (int i = 0; i < NUM_SELECTED; ++i)
        if (SELECTED_IDS[i] == cid) return true;
    return false;
}

static inline const char* label_for_cid(int cid) {
    if (cid >= 0 && cid < NUM_COCO_CLASSES) return CLASS_NAMES[cid];
    return "unknown";
}

// 2D cross product
static inline double cross2d(double ux, double uy, double vx, double vy) {
    return ux * vy - uy * vx;
}

// Per-track state for line crossing
struct TrackState {
    int last_side;       // +1 or -1
    double last_x, last_y;
    int sequence;
};

// Per-class per-direction counts
struct DirCount {
    int left_to_right;
    int right_to_left;
};

// Crossing event for current frame
struct CrossingEvent {
    uint64_t track_id;
    int class_id;
    std::string label;
    std::string direction;
    std::string event_id;
    double ix, iy; // intersection point
};

// Generate deterministic colors for up to 80 classes (seeded like numpy rng(3))
static cv::Scalar get_class_color(int cid) {
    // Simple deterministic hash-based color
    unsigned seed = (unsigned)(cid * 7 + 13);
    int r = (int)((seed * 2654435761u) & 0xFF);
    int g = (int)(((seed + 1) * 2654435761u) & 0xFF);
    int b = (int)(((seed + 2) * 2654435761u) & 0xFF);
    return cv::Scalar(b, g, r);
}

extern "C" bool NvDsCustomPostProcess(NvDsCustomPostProcessFrameInCpu *in) {
    if (!in || !in->Y_host || !in->UV_host) return false;
    const int W = in->W, H = in->H;
    if (W < 2 || H < 2 || (W & 1) || (H & 1)) {
        fprintf(stderr, "[line_crossing_render] surface must be even-sized, got %dx%d\n", W, H);
        return false;
    }

    NvDsInferTensorMeta *tm = in->num_tensor_metas
        ? (NvDsInferTensorMeta *) in->tensor_metas[0] : nullptr;
    const RsMeta *rs = find_rs_meta((NvDsFrameMeta *) in->frame_meta);
    (void) tm; (void) rs;

    // ==== BEGIN GENERATED PROCESS ====

    // Per-track crossing state — must persist across frames
    static std::map<uint64_t, TrackState> track_states;
    // Per-class counts — must persist across frames
    static std::map<std::string, DirCount> counts;
    // Counted event IDs to suppress duplicates
    static std::set<std::string> counted_event_ids;
    // Initialize counts on first call
    static bool counts_initialized = false;
    if (!counts_initialized) {
        for (int i = 0; i < NUM_COUNT_LABELS; ++i) {
            DirCount dc; dc.left_to_right = 0; dc.right_to_left = 0;
            counts[std::string(COUNT_LABELS[i])] = dc;
        }
        counts_initialized = true;
    }

    // Get frame meta for accessing object metas (tracked objects)
    NvDsFrameMeta *frame_meta = (NvDsFrameMeta *) in->frame_meta;

    // Collect all tracked objects from NvDsObjectMeta
    struct TrackInfo {
        uint64_t track_id;
        int class_id;
        std::string label;
        float score;
        float left, top, width, height;
        float cx, cy; // bbox center
    };

    std::vector<TrackInfo> tracks;
    if (frame_meta) {
        for (NvDsMetaList *ol = frame_meta->obj_meta_list; ol; ol = ol->next) {
            NvDsObjectMeta *obj = (NvDsObjectMeta *) ol->data;
            if (!obj) continue;
            int cid = (int) obj->class_id;
            if (!is_selected(cid)) continue;

            TrackInfo ti;
            ti.track_id = obj->object_id;
            ti.class_id = cid;
            ti.label = std::string(label_for_cid(cid));
            ti.score = obj->confidence;
            ti.left = obj->rect_params.left;
            ti.top = obj->rect_params.top;
            ti.width = obj->rect_params.width;
            ti.height = obj->rect_params.height;
            ti.cx = ti.left + ti.width * 0.5f;
            ti.cy = ti.top + ti.height * 0.5f;
            tracks.push_back(ti);
        }
    }

    // ── Node 6: Line-crossing event detection ──
    std::vector<CrossingEvent> events;

    for (size_t i = 0; i < tracks.size(); ++i) {
        const TrackInfo &tr = tracks[i];
        uint64_t tid = tr.track_id;
        double px = (double) tr.cx;
        double py = (double) tr.cy;

        // Compute signed value: cross(line_vector, point - a)
        double dx = px - LINE_AX;
        double dy = py - LINE_AY;
        double signed_val = cross2d(LINE_VX, LINE_VY, dx, dy);

        int side = 0;
        if (signed_val > 0.0) side = 1;
        else if (signed_val < 0.0) side = -1;

        if (side == 0) continue; // on the line, skip

        std::map<uint64_t, TrackState>::iterator it = track_states.find(tid);
        if (it != track_states.end()) {
            TrackState &ts = it->second;
            if (ts.last_side != side) {
                // Side changed — check segment intersection
                double prev_x = ts.last_x;
                double prev_y = ts.last_y;
                double travel_x = px - prev_x;
                double travel_y = py - prev_y;

                double denom = cross2d(travel_x, travel_y, LINE_VX, LINE_VY);
                if (std::abs(denom) > 1e-12) {
                    double disp_x = LINE_AX - prev_x;
                    double disp_y = LINE_AY - prev_y;
                    double t_param = cross2d(disp_x, disp_y, LINE_VX, LINE_VY) / denom;
                    double u_param = cross2d(disp_x, disp_y, travel_x, travel_y) / denom;
                    if (t_param >= 0.0 && t_param <= 1.0 && u_param >= 0.0 && u_param <= 1.0) {
                        const char *direction = (ts.last_side > 0) ? "left_to_right" : "right_to_left";
                        ts.sequence += 1;

                        CrossingEvent ev;
                        ev.track_id = tid;
                        ev.class_id = tr.class_id;
                        ev.label = tr.label;
                        ev.direction = std::string(direction);

                        std::ostringstream eid_ss;
                        eid_ss << tid << ":" << ts.sequence;
                        ev.event_id = eid_ss.str();

                        ev.ix = prev_x + t_param * travel_x;
                        ev.iy = prev_y + t_param * travel_y;
                        events.push_back(ev);
                    }
                }
            }
            // Update state
            ts.last_side = side;
            ts.last_x = px;
            ts.last_y = py;
        } else {
            // First observation of this track
            TrackState ns;
            ns.last_side = side;
            ns.last_x = px;
            ns.last_y = py;
            ns.sequence = 0;
            track_states[tid] = ns;
        }
    }

    // ── Node 7: Directional class count accumulation ──
    for (size_t i = 0; i < events.size(); ++i) {
        const CrossingEvent &ev = events[i];
        if (counted_event_ids.find(ev.event_id) == counted_event_ids.end()) {
            counted_event_ids.insert(ev.event_id);
            std::map<std::string, DirCount>::iterator cit = counts.find(ev.label);
            if (cit != counts.end()) {
                if (ev.direction == "left_to_right")
                    cit->second.left_to_right += 1;
                else
                    cit->second.right_to_left += 1;
            }
        }
    }

    int total_crossings = 0;
    for (std::map<std::string, DirCount>::const_iterator cit = counts.begin(); cit != counts.end(); ++cit) {
        total_crossings += cit->second.left_to_right + cit->second.right_to_left;
    }

    // ── Node 9: Draw overlay ──
    cv::Mat frame = read_nv12_bgr(in);

    // Draw counting line (yellow)
    cv::line(frame, cv::Point((int)LINE_AX, (int)LINE_AY),
             cv::Point((int)LINE_BX, (int)LINE_BY),
             cv::Scalar(0, 255, 255), 2, cv::LINE_AA);

    // Draw tracked objects with boxes and captions
    for (size_t i = 0; i < tracks.size(); ++i) {
        const TrackInfo &tr = tracks[i];
        int x1 = (int) tr.left;
        int y1 = (int) tr.top;
        int x2 = (int)(tr.left + tr.width);
        int y2 = (int)(tr.top + tr.height);
        cv::Scalar color = get_class_color(tr.class_id);
        cv::rectangle(frame, cv::Point(x1, y1), cv::Point(x2, y2), color, 2, cv::LINE_AA);

        char caption[128];
        snprintf(caption, sizeof(caption), "%s ID %lu %d%%",
                 tr.label.c_str(), (unsigned long)tr.track_id,
                 (int)(tr.score * 100.0f));
        int ty = std::max(18, y1 - 5);
        cv::putText(frame, caption, cv::Point(x1, ty),
                    cv::FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv::LINE_AA);
    }

    // Draw per-class counts in top-left
    for (int row = 0; row < NUM_COUNT_LABELS; ++row) {
        std::map<std::string, DirCount>::const_iterator cit = counts.find(std::string(COUNT_LABELS[row]));
        int l2r = 0, r2l = 0;
        if (cit != counts.end()) {
            l2r = cit->second.left_to_right;
            r2l = cit->second.right_to_left;
        }
        char text[128];
        snprintf(text, sizeof(text), "%s: L>R %d  R>L %d", COUNT_LABELS[row], l2r, r2l);

        // Background rectangle for readability
        int baseline = 0;
        cv::Size tsz = cv::getTextSize(text, cv::FONT_HERSHEY_SIMPLEX, 0.58, 2, &baseline);
        int tx = 12, tty = 25 + 24 * row;
        cv::rectangle(frame, cv::Point(tx - 2, tty - tsz.height - 2),
                      cv::Point(tx + tsz.width + 2, tty + baseline + 2),
                      cv::Scalar(0, 0, 0), cv::FILLED);
        cv::putText(frame, text, cv::Point(tx, tty),
                    cv::FONT_HERSHEY_SIMPLEX, 0.58, cv::Scalar(255, 255, 255), 2, cv::LINE_AA);
    }

    // Total crossings
    {
        char total_text[64];
        snprintf(total_text, sizeof(total_text), "Total crossings: %d", total_crossings);
        int tx = 12, tty = 190;
        int baseline = 0;
        cv::Size tsz = cv::getTextSize(total_text, cv::FONT_HERSHEY_SIMPLEX, 0.7, 2, &baseline);
        cv::rectangle(frame, cv::Point(tx - 2, tty - tsz.height - 2),
                      cv::Point(tx + tsz.width + 2, tty + baseline + 2),
                      cv::Scalar(0, 0, 0), cv::FILLED);
        cv::putText(frame, total_text, cv::Point(tx, tty),
                    cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(0, 255, 255), 2, cv::LINE_AA);
    }

    write_nv12(frame, in);

    // ── Publish metadata via render_meta::Builder ──
    render_meta::Builder sb(W, H);

    // Publish each crossing event as a polyline (the travel segment)
    for (size_t i = 0; i < events.size(); ++i) {
        const CrossingEvent &ev = events[i];
        // Find the track's previous position from state to draw the crossing segment
        std::vector<double> seg_xy;
        seg_xy.push_back(ev.ix);
        seg_xy.push_back(ev.iy);
        std::string elabel = ev.label + " " + ev.direction;
        sb.polyline(seg_xy, elabel.c_str());
    }

    // Publish the counting line itself
    {
        std::vector<double> line_xy;
        line_xy.push_back(LINE_AX);
        line_xy.push_back(LINE_AY);
        line_xy.push_back(LINE_BX);
        line_xy.push_back(LINE_BY);
        sb.polyline(line_xy, "counting_line");
    }

    // Publish per-class counts as scalar fields
    for (int i = 0; i < NUM_COUNT_LABELS; ++i) {
        std::map<std::string, DirCount>::const_iterator cit = counts.find(std::string(COUNT_LABELS[i]));
        if (cit != counts.end()) {
            std::string key_l2r = std::string(COUNT_LABELS[i]) + "_l2r";
            std::string key_r2l = std::string(COUNT_LABELS[i]) + "_r2l";
            sb.field_i(key_l2r.c_str(), cit->second.left_to_right);
            sb.field_i(key_r2l.c_str(), cit->second.right_to_left);
        }
    }
    sb.field_i("total_crossings", total_crossings);

    // Publish each active track as a box
    for (size_t i = 0; i < tracks.size(); ++i) {
        const TrackInfo &tr = tracks[i];
        sb.box((double)tr.left, (double)tr.top, (double)tr.width, (double)tr.height,
               tr.label.c_str(), (int)tr.track_id, (double)tr.score);
    }

    // Publish crossing events as fields
    sb.field_i("num_events", (int)events.size());
    for (size_t i = 0; i < events.size(); ++i) {
        const CrossingEvent &ev = events[i];
        std::string pfx = "event_" + std::to_string(i);
        sb.field_s((pfx + "_id").c_str(), ev.event_id.c_str());
        sb.field_i((pfx + "_track_id").c_str(), (int)ev.track_id);
        sb.field_s((pfx + "_label").c_str(), ev.label.c_str());
        sb.field_s((pfx + "_direction").c_str(), ev.direction.c_str());
        sb.field_d((pfx + "_ix").c_str(), ev.ix);
        sb.field_d((pfx + "_iy").c_str(), ev.iy);
    }

    sb.publish(in->frame_meta);

    // ==== END GENERATED PROCESS ====
    return true;
}

CHECK_NVCUSTOMPROCESS_CPU_PROTOTYPE(NvDsCustomPostProcess);