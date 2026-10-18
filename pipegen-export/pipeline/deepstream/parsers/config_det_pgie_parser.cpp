// Custom detection (bbox) parser (generated).
// Scaffold validates the output layer and exposes the raw tensor(s); the DECODE
// block (per-model) populates `objectList` with NvDsInferObjectDetectionInfo.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "nvdsinfer_custom_impl.h"

extern "C" bool ParseConfigDetPgie(
    std::vector<NvDsInferLayerInfo> const& outputLayersInfo,
    NvDsInferNetworkInfo const& networkInfo,
    NvDsInferParseDetectionParams const& detectionParams,
    std::vector<NvDsInferObjectDetectionInfo>& objectList);

CHECK_CUSTOM_PARSE_FUNC_PROTOTYPE(ParseConfigDetPgie);

extern "C" bool ParseConfigDetPgie(
    std::vector<NvDsInferLayerInfo> const& outputLayersInfo,
    NvDsInferNetworkInfo const& networkInfo,
    NvDsInferParseDetectionParams const& detectionParams,
    std::vector<NvDsInferObjectDetectionInfo>& objectList)
{
    if (outputLayersInfo.empty()) return false;
    auto const& layer0 = outputLayersInfo[0];

    const unsigned numClasses = detectionParams.numClassesConfigured;
    const float netW = static_cast<float>(networkInfo.width);
    const float netH = static_cast<float>(networkInfo.height);
    const float* data = static_cast<const float*>(layer0.buffer);

    static bool logged = false;
    if (!logged) {
        logged = true;
        fprintf(stderr, "[ParseConfigDetPgie] first call: layer=%s numDims=%d "
                "networkInput=%.0fx%.0f numClasses=%u outputs=%zu\n",
                layer0.layerName ? layer0.layerName : "?",
                layer0.inferDims.numDims, netW, netH, numClasses,
                outputLayersInfo.size());
    }

    // ==== BEGIN GENERATED DECODE ====
    // YOLOv8 output shape (batch stripped): [84, N]
    // where 84 = 4 (cx,cy,w,h) + 80 class scores, N = number of proposals.
    // The tensor is in [featureDim, numProposals] layout; we must transpose.

    // Derive dimensions from layer0.inferDims at runtime.
    // Expected: numDims=2, d[0]=84, d[1]=N  (or d[0]=N, d[1]=84 if transposed).
    if (layer0.inferDims.numDims < 2) return false;

    unsigned dim0 = layer0.inferDims.d[0];
    unsigned dim1 = layer0.inferDims.d[1];

    // Identify which dimension is the feature dim (4 + numClasses) and which is proposals.
    unsigned featureDim = 4u + numClasses; // expected 84
    unsigned numProposals = 0;
    bool transposed = false; // true if layout is already [N, 84]

    if (dim0 == featureDim) {
        // Layout: [featureDim, N] — standard YOLOv8 export
        numProposals = dim1;
        transposed = false;
    } else if (dim1 == featureDim) {
        // Layout: [N, featureDim] — already transposed
        numProposals = dim0;
        transposed = true;
    } else {
        fprintf(stderr, "[ParseConfigDetPgie] unexpected dims: d[0]=%u d[1]=%u featureDim=%u\n",
                dim0, dim1, featureDim);
        return false;
    }

    // Helper lambda to access element (proposal p, feature f)
    // For [featureDim, N]:  index = f * N + p
    // For [N, featureDim]:  index = p * featureDim + f
    auto elem = [&](unsigned p, unsigned f) -> float {
        if (transposed)
            return data[p * featureDim + f];
        else
            return data[f * numProposals + p];
    };

    for (unsigned p = 0; p < numProposals; ++p) {
        // Find best class score (scores are already post-sigmoid in Ultralytics export)
        float maxScore = 0.0f;
        unsigned bestClass = 0;
        for (unsigned c = 0; c < numClasses; ++c) {
            float s = elem(p, 4 + c);
            if (s > maxScore) {
                maxScore = s;
                bestClass = c;
            }
        }

        // Per-class threshold
        float thr = (bestClass < detectionParams.perClassPreclusterThreshold.size())
                     ? detectionParams.perClassPreclusterThreshold[bestClass]
                     : 0.3f;
        if (maxScore < thr) continue;

        // cx, cy, w, h in network-input pixel coordinates
        float cx = elem(p, 0);
        float cy = elem(p, 1);
        float bw = elem(p, 2);
        float bh = elem(p, 3);

        // Convert centre-size to top-left corner + size
        float left = cx - bw * 0.5f;
        float top  = cy - bh * 0.5f;

        // Clamp to network input
        left = std::max<float>(0.0f, std::min<float>(left, netW));
        top  = std::max<float>(0.0f, std::min<float>(top,  netH));
        bw   = std::max<float>(0.0f, std::min<float>(bw,   netW - left));
        bh   = std::max<float>(0.0f, std::min<float>(bh,   netH - top));

        // Skip degenerate boxes
        if (bw < 1.0f || bh < 1.0f) continue;

        NvDsInferObjectDetectionInfo obj;
        obj.classId = bestClass;
        obj.left = left;
        obj.top = top;
        obj.width = bw;
        obj.height = bh;
        obj.detectionConfidence = maxScore;
        objectList.push_back(obj);
    }
    // ==== END GENERATED DECODE ====
    return true;
}