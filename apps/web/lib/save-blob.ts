// Trigger a browser download of a Blob. This is the few lines file-saver does
// internally for modern browsers, inlined to avoid file-saver's CJS/ESM interop
// problem: its module.exports IS the function (no `.default`, only a `.saveAs`
// own-property), and webpack's production interop of that shape did not expose
// the named `{ saveAs }` binding from a dynamic import, so it resolved to
// undefined in prod and every Word/Excel download threw "saveAs is not a
// function". A native object-URL + anchor click has no interop surface and
// behaves identically in dev and prod.

export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Give the browser a tick to start the download before revoking the URL.
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
