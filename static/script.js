let cropper = null;
let video = null;
let capturedBlob = null;

/* ---------------- Upload Preview ---------------- */

document.addEventListener("DOMContentLoaded", function(){

const fileInput = document.getElementById("imageInput");

if(fileInput){

fileInput.addEventListener("change", function(){

const file = this.files[0];
if(!file) return;

const scanImage = document.getElementById("scanImage");
const camera = document.getElementById("camera");

/* destroy cropper */
if(cropper){
cropper.destroy();
cropper = null;
}

/* show uploaded image */
scanImage.src = URL.createObjectURL(file);
scanImage.style.display = "block";

/* hide camera */
camera.style.display = "none";

/* clear captured image */
capturedBlob = null;

/* stop camera if running */
if(camera.srcObject){
camera.srcObject.getTracks().forEach(track => track.stop());
camera.srcObject = null;
}

document.getElementById("result").classList.add("hidden");

});

}

});


/* ---------------- Start Crop ---------------- */

function startCrop(){

const image = document.getElementById("scanImage");

if(!image.src || image.style.display === "none"){
alert("Upload or capture an image first");
return;
}

/* destroy old cropper */

if(cropper){
cropper.destroy();
cropper = null;
}

/* start cropper */

cropper = new Cropper(image,{
aspectRatio:1,
viewMode:1,
autoCropArea:0.8
});

}


/* ---------------- Apply Crop ---------------- */

function applyCrop(){

if(!cropper){
alert("Start crop first");
return;
}

/* crop image EXACT model size */

const canvas = cropper.getCroppedCanvas({
width:224,
height:224
});

const scanImage = document.getElementById("scanImage");

/* show cropped image */

scanImage.src = canvas.toDataURL("image/jpeg");

/* convert cropped image to blob */

canvas.toBlob(function(blob){

capturedBlob = blob;

},"image/jpeg",0.95);

/* destroy cropper */

cropper.destroy();
cropper = null;

}


/* ---------------- Camera ---------------- */

function openCamera(){

video = document.getElementById("camera");
const scanImage = document.getElementById("scanImage");

/* destroy cropper */

if(cropper){
cropper.destroy();
cropper = null;
}

navigator.mediaDevices.getUserMedia({
video:{facingMode:{ideal:"environment"}}
})
.then(stream=>{

video.srcObject = stream;
video.style.display="block";
scanImage.style.display="none";

})
.catch(()=>{

navigator.mediaDevices.getUserMedia({video:true})
.then(stream=>{

video.srcObject = stream;
video.style.display="block";
scanImage.style.display="none";

})
.catch(err=>{
console.error(err);
alert("Camera access denied.");
});

});

}


/* ---------------- Capture Photo ---------------- */

function capturePhoto(){

if(!video || !video.srcObject){
alert("Please open camera first");
return;
}

const canvas = document.getElementById("canvas");
const context = canvas.getContext("2d");

canvas.width = video.videoWidth;
canvas.height = video.videoHeight;

context.drawImage(video,0,0);

const scanImage = document.getElementById("scanImage");

/* show captured image */

scanImage.src = canvas.toDataURL("image/jpeg");
scanImage.style.display = "block";

/* clear upload */

document.getElementById("imageInput").value = "";

/* stop camera */

video.srcObject.getTracks().forEach(track => track.stop());
video.srcObject = null;
video.style.display = "none";

/* store blob */

canvas.toBlob(function(blob){
capturedBlob = blob;
},"image/jpeg");

}


/* ---------------- Predict ---------------- */

function predict(){

const input = document.getElementById("imageInput");
const formData = new FormData();
const scanLine = document.getElementById("scanLine");

/* priority: cropped/captured image */

if(capturedBlob){
formData.append("file", capturedBlob, "capture.jpg");
}

/* uploaded image */

else if(input.files && input.files.length > 0){
formData.append("file", input.files[0]);
}

else{
alert("Please upload or capture an image");
return;
}

/* start scan animation */

scanLine.classList.add("scan-active");

fetch("/predict",{
method:"POST",
body:formData
})
.then(res => res.json())
.then(data => {

setTimeout(()=>{

scanLine.classList.remove("scan-active");
showResult(data);

},2000);

})
.catch(err => {

scanLine.classList.remove("scan-active");

console.error(err);
alert("Prediction failed.");

});

}


/* ---------------- Show Result ---------------- */

function showResult(data){

const resultBox = document.getElementById("result");
const predictionText = document.getElementById("predictionText");
const confidenceText = document.getElementById("confidenceText");
const confidenceFill = document.getElementById("confidenceFill");
const treatmentText = document.getElementById("treatmentText");
const preventionText = document.getElementById("preventionText");

resultBox.classList.remove("hidden");

let prediction = data.prediction || "Unknown";

/* format crop + disease */

if(prediction.includes("___")){

let parts = prediction.split("___");
let crop = parts[0];
let disease = parts[1].replace(/_/g," ");

predictionText.innerText =
"Crop: " + crop + " | Disease: " + disease;

}else{

predictionText.innerText = prediction;

}

/* confidence */

let confidence = data.confidence || 0;
let percent = (confidence*100).toFixed(2);

confidenceText.innerText =
"Confidence: " + percent + "%";

confidenceFill.style.width =
percent + "%";

/* treatment */

treatmentText.innerText =
"Treatment: " + (data.treatment || "No data available");

preventionText.innerText =
"Prevention: " + (data.prevention || "No data available");

}


/* ---------------- Reset ---------------- */

function resetScan(){

document.getElementById("result").classList.add("hidden");

const scanImage = document.getElementById("scanImage");
const camera = document.getElementById("camera");

/* destroy cropper */

if(cropper){
cropper.destroy();
cropper = null;
}

scanImage.style.display = "none";
scanImage.src = "";

document.getElementById("imageInput").value = "";

capturedBlob = null;

/* stop camera */

if(camera.srcObject){
camera.srcObject.getTracks().forEach(track => track.stop());
camera.srcObject = null;
}

camera.style.display = "none";

}


/* ---------------- Service Worker ---------------- */

if ("serviceWorker" in navigator) {

window.addEventListener("load", function(){

navigator.serviceWorker.register("/static/service-worker.js")
.then(function(){
console.log("Service Worker Registered");
})
.catch(function(err){
console.log("Service Worker Error:", err);
});

});

}