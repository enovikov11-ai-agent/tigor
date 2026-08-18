console.log("Model loaded");

const model = (function() {
  let isAlertOpened = false;
  function alertUI(text, callback) {
    isAlertOpened = true;
    view.controls.enabled = false;
    $("#dialog").text(text);
    $("#dialog").dialog({
      close: () => {
        setTimeout(() => {
          isAlertOpened = false;
          view.controls.enabled = true;
          callback();
        }, 20);
      }
    });
  }

  if (/file/.test(location.href)) {
    document.title = "[ТЕСТ] Сфериум";
  }
  if (localStorage.shown != "1") {
    localStorage.shown = "1";
    help();
  }

  function help() {
    alertUI(settings.lang.hello, () => {});
  }

  function checkWin(state = view.getState()) {
    for (let triplet of settings.winningTriplets) {
      if (
        state[triplet[0]] == 1 &&
        state[triplet[1]] == 1 &&
        state[triplet[2]] == 1
      ) {
        return 1;
      }
      if (
        state[triplet[0]] == 2 &&
        state[triplet[1]] == 2 &&
        state[triplet[2]] == 2
      ) {
        return 2;
      }
    }
    return -1;
  }

  let now;
  refresh();

  function onFaceClick(faceid) {
    if (isAlertOpened) {
      return;
    }
    if (view.getState()[faceid] != -1) {
      return;
    }
    view.paintFace(faceid, now);
    now = now == 1 ? 2 : 1;
    let maybeWin = checkWin();
    if (maybeWin == -1) {
      return;
    }
    controller.stopClickMonitoring();
    setTimeout(() => {
      alertUI(settings.lang["winner" + maybeWin], refresh);
    }, 40);
  }

  function refresh() {
    now = 1;
    controller.startClickMonitoring(onFaceClick);
    view.reset();
  }

  return { refresh, help };
})();
