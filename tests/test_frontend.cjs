'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {Stabilizer, cameraError} = require('../frontend/static/core.js');
const Camera = require('../frontend/static/camera.js');
test('three-frame stabilization immediately clears an old label on a dark frame', () => {
  const s = new Stabilizer();const p = {status:'OK',label:'Early Blight'};
  assert.equal(s.push(p).ready,false);assert.equal(s.push(p).ready,false);assert.equal(s.push(p).ready,true);
  assert.equal(s.push({status:'LOW_QUALITY',label:null}).ready,false);assert.equal(s.label,null);
  assert.equal(s.push(p).count,1);
});
test('permission probe releases tracks and exact selected device is requested', async () => {
  let stops=0;const requested=[];const track={label:'QA USB',getSettings:()=>({deviceId:'usb-id'}),stop:()=>stops++,addEventListener:()=>{}};
  const stream={getTracks:()=>[track],getVideoTracks:()=>[track]};
  const devices={getUserMedia:async c=>{requested.push(c);return stream;},enumerateDevices:async()=>[{kind:'videoinput',deviceId:'built-in',label:'Integrated'},{kind:'videoinput',deviceId:'usb-id',label:'USB'}]};
  const video={pause(){},async play(){},srcObject:null};const c=new Camera(video,devices);
  assert.equal((await c.enumerate(true)).length,2);assert.equal(stops,1);assert.equal(c.stream,null);
  const result=await c.start('usb-id');assert.equal(requested[1].video.deviceId.exact,'usb-id');assert.equal(result.deviceId,'usb-id');
  c.pause();assert(c.paused);await c.resume();assert(!c.paused);c.stop();assert.equal(c.stream,null);assert.equal(stops,2);
});
test('device mismatch fails and releases the incorrect stream', async()=>{
  let stopped=false;const t={getSettings:()=>({deviceId:'built-in'}),stop:()=>{stopped=true;}};
  const c=new Camera({pause(){}},{getUserMedia:async()=>({getVideoTracks:()=>[t],getTracks:()=>[t]})});
  await assert.rejects(c.start('usb-id'),e=>e.name==='OverconstrainedError');assert(stopped);assert.equal(c.stream,null);
});
test('permission and occupied-device errors are actionable',()=>{
  assert.match(cameraError({name:'NotAllowedError'}),/permission denied/);assert.match(cameraError({name:'NotReadableError'}),/occupied/);
});
test('review-required predictions stabilize without being treated as confirmed diagnoses',()=>{
 const s=new Stabilizer(2);assert.equal(s.push({status:'REVIEW',label:'Early Blight'}).ready,false);assert.equal(s.push({status:'REVIEW',label:'Early Blight'}).ready,true);
 assert.equal(s.push({status:'NO_DETECTION',label:null}).ready,false);assert.equal(s.label,null);
});
