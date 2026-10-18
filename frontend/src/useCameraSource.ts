import {useEffect,useRef,useState,type RefObject} from 'react';
export type CameraSource='simulated_usb'|'existing_video'|'physical_usb';
export type ReplayPacket={frame_id:number;relative_seconds:number;pts_ns:number;width:number;height:number;detections:any[];events:any[];stats:any;summary:any};
export function useCameraSource(mode:'real'|'synthetic',video:RefObject<HTMLVideoElement|null>){
 const [source,setSource]=useState<CameraSource>('simulated_usb'),[packet,setPacket]=useState<ReplayPacket|null>(null),[notice,setNotice]=useState(''),[hardware,setHardware]=useState('Checking camera availability…'),[ready,setReady]=useState(false);
 const sourceRef=useRef(source);sourceRef.current=source;
 const epoch=useRef(0),zero=useRef<ReplayPacket|null>(null);
 const fallback=()=>{if(sourceRef.current!=='simulated_usb')return;epoch.current++;sourceRef.current='existing_video';setSource('existing_video');setReady(false);setPacket(null);setNotice('The simulated camera is unavailable. We switched to Recorded Video so you can keep watching.')};
 function select(value:CameraSource){epoch.current++;setNotice('');setReady(false);setPacket(null);setSource(value)}
 function restart(){epoch.current++;setPacket(zero.current);if(video.current){video.current.currentTime=0;video.current.playbackRate=1;video.current.play().catch(()=>setNotice('Press Start to begin the recorded replay.'))}}
 function toggle(){const v=video.current;if(!v)return;if(v.paused)v.play().catch(()=>setNotice('Press the video play control to begin.'));else v.pause()}
 useEffect(()=>{
  if(mode!=='real'||source!=='simulated_usb')return;
  let disposed=false,busy=false,lastTime=-1,failures=0;setReady(false);setPacket(null);zero.current=null;
  async function tick(){if(disposed||busy)return;const time=video.current?.currentTime||0;if(time===lastTime)return;busy=true;const generation=epoch.current;
   try{const response=await fetch(`/api/replay?seconds=${encodeURIComponent(time)}`,{signal:AbortSignal.timeout(4000)});if(!response.ok)throw Error('Replay unavailable');const next:ReplayPacket=await response.json();if(!next.summary?.available||!next.stats||!Array.isArray(next.events))throw Error('Replay incomplete');if(disposed||generation!==epoch.current)return;if(Math.abs((video.current?.currentTime||0)-time)>.5&&!video.current?.paused)throw Error('Replay cannot keep up');if(time<.04)zero.current=next;setPacket(next);setReady(true);failures=0;lastTime=time}
   catch{if(!disposed&&generation===epoch.current){failures++;if(failures>=2){disposed=true;fallback()}}}finally{busy=false}}
  tick();const timer=setInterval(tick,80);return()=>{disposed=true;clearInterval(timer)};
 },[source,mode]);
 useEffect(()=>{if(mode!=='real'||source!=='physical_usb')return;let disposed=false;setHardware('Checking camera availability…');if(!navigator.mediaDevices?.enumerateDevices){setHardware('Camera discovery is unavailable in this browser. No USB camera has been verified.');return}navigator.mediaDevices.enumerateDevices().then(devices=>{if(!disposed)setHardware(devices.some(d=>d.kind==='videoinput')?'A camera input is available, but a compatible USB camera has not been verified. AI analysis is unavailable.':'No USB camera detected')}).catch(()=>{if(!disposed)setHardware('Camera access is unavailable. No USB camera has been verified.')});return()=>{disposed=true}},[source,mode]);
 return {source,packet,notice,hardware,ready,select,restart,toggle,fallback};
}
