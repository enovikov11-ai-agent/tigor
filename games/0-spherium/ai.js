console.log("AI loaded");
const MAX_DEPTH = 5;

function getWinProbability(state, player, depth = 0) {
  if (depth >= MAX_DEPTH) {
    return 0.5;
  }
  let maybeWin = checkWin(state);
  if (maybeWin == 1) {
    return 1 == player ? 1 : 0;
  } else if (maybeWin == 2) {
    return 2 == player ? 1 : 0;
  }

  let emptyIds = getEmptyIds();
  if (emptyIds.length == 0) {
    return 0;
  }
  //дописать
}

function getEmptyIds() {
  return facesState.map((e, i) => (e == -1 ? i : -1)).filter(e => e != -1);
}

function getStep(player) {
  let emptyIds = getEmptyIds(),
    maxProb = 0,
    step = -1;
  if (emptyIds.length == 0) {
    return -1;
  }
  for (let id of emptyIds) {
    let newState = Array.from(facesState);
    newState[id] = player;
    let prob = getWinProbability(newState, player);
    if (prob > maxProb) {
      maxProb = prob;
      step = id;
    }
  }
  return step;
}
