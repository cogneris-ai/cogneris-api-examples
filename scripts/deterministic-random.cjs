let state = 0x5854524b;

Math.random = () => {
  state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
  return state / 0x100000000;
};
