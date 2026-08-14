(() => {
  const canvas = $0;

  const stream = canvas.captureStream(60);

  const mimeType =
    ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm"]
      .find(t => MediaRecorder.isTypeSupported(t));

  const chunks = [];

  const recorder = new MediaRecorder(stream, {
    mimeType,
    videoBitsPerSecond: 8_000_000
  });

  recorder.ondataavailable = e => {
    if (e.data.size) chunks.push(e.data);
  };

  recorder.onstop = () => {
    const blob = new Blob(chunks, { type: mimeType });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "canvas-recording.webm";
    a.click();
  };

  recorder.start(1000);

  window.stopCanvasRecording = () => recorder.stop();

  console.log("Recording started.");
  console.log("Run stopCanvasRecording() to stop and download.");
})();