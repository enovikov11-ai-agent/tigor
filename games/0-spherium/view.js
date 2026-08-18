console.log("View loaded");

const view = (function() {
  //Основные объекты
  let scene = new THREE.Scene(),
    camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    ),
    light = new THREE.HemisphereLight(0xffffbb, 0x080820, 1),
    controls = new THREE.OrbitControls(camera),
    renderer = new THREE.WebGLRenderer(),
    //Геометрия
    geometry = settings.createSpheriumGeometry(),
    state,
    material = new THREE.MeshLambertMaterial({
      vertexColors: THREE.FaceColors
    }),
    mesh = new THREE.Mesh(geometry, material),
    wireGeometry = new THREE.EdgesGeometry(geometry),
    wireMaterial = new THREE.LineBasicMaterial({ color: 0, linewidth: 2 }),
    wireMesh = new THREE.LineSegments(wireGeometry, wireMaterial);

  function animate() {
    light.position.copy(camera.position);
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }

  function reset() {
    state = new Array(geometry.faces.length).fill(-1);
    camera.position.set(0, 0, 25);
    geometry.faces.forEach(face => face.color.setHex(settings.colors.neutral));
    geometry.colorsNeedUpdate = true;
  }

  //Запуск отображения
  reset();
  scene.add(light);
  scene.add(mesh);
  scene.add(wireMesh);
  controls.enablePan = false;
  controls.enableZoom = false;
  controls.update();
  scene.background = new THREE.Color(0xf0f0f0);
  renderer.setSize(window.innerWidth, window.innerHeight);
  document.body.appendChild(renderer.domElement);
  animate();

  window.onresize = () => {
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
  };

  return {
    paintFace(id, color) {
      state[id] = color;
      let hexColor = settings.colors.neutral;
      if (color == 1) {
        hexColor = settings.colors.player1;
      }
      if (color == 2) {
        hexColor = settings.colors.player2;
      }
      geometry.faces[id].color.setHex(hexColor);
      geometry.colorsNeedUpdate = true;
    },
    reset,
    getState() {
      return Array.from(state);
    },
    mesh,
    camera,
    controls
  };
})();

console.log("View ended");
