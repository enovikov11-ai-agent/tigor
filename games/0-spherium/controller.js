console.log("Controller loaded");
const controller = (function() {
  let onClick = () => {},
    raycaster = new THREE.Raycaster(),
    mouse = new THREE.Vector2(),
    isMoved = false,
    clickedAt = 0;

  window.addEventListener(
    "mousemove",
    e => {
      isMoved = true;
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    },
    false
  );

  window.addEventListener(
    "mousedown",
    () => {
      clickedAt = Date.now();
      isMoved = false;
    },
    false
  );

  window.addEventListener(
    "click",
    () => {
      if (isMoved && Date.now() - clickedAt > 120) {
        return;
      }
      raycaster.setFromCamera(mouse, view.camera);
      let intersects = raycaster.intersectObject(view.mesh);
      if (intersects.length == 0) {
        return;
      }
      onClick(intersects[0].faceIndex);
    },
    false
  );

  return {
    startClickMonitoring(callback) {
      onClick = callback;
    }, //callback(face)
    stopClickMonitoring() {
      onClick = () => {};
      isMoved = false;
      clickedAt = 0;
    }
  };
})();
