export function scaleLinear(d0, d1, r0, r1) {
  return (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
}

export function scaleLog(d0, d1, r0, r1) {
  const l0 = Math.log(d0);
  const l1 = Math.log(d1);
  return (v) => r0 + ((Math.log(v) - l0) / (l1 - l0)) * (r1 - r0);
}
