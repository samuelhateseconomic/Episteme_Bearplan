export function savedDuration(microseconds: number): string {
  const minutes = Math.floor(microseconds / 60_000_000);
  const seconds = (microseconds % 60_000_000) / 1_000_000;
  return `${minutes} min ${seconds.toLocaleString(undefined, { maximumFractionDigits: 6 })} s`;
}
