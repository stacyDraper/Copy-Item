#!/usr/bin/env python3
import sys, os, subprocess, hashlib, shutil
from pathlib import Path
def sha256(p: Path) -> str:
  h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def verify_manifest(folder: Path):
  mf=folder/"MANIFEST.sha256"
  if not mf.exists(): print("[warn] no MANIFEST.sha256"); return
  ok=True
  for raw in mf.read_text().splitlines():
    line=raw.strip();  # "hash␠␠path"
    if not line: continue
    parts=line.split("  ",1)
    if len(parts)!=2: print("[ERR] bad manifest:",raw); ok=False; continue
    digest,name=parts; fp=(folder/name) if not Path(name).is_absolute() else Path(name)
    if not fp.exists(): print("[ERR] missing in pack:",name); ok=False; continue
    if sha256(fp)!=digest: print("[ERR] hash mismatch:",name); ok=False
  if not ok: sys.exit(2)
  print("[ok] proposal manifest verified.")
def apply_patches(folder: Path) -> bool:
  pd=folder/"patches"
  if not pd.exists(): return False
  patches=sorted(pd.glob("*.diff"))
  if not patches: return False
  for p in patches:
    print("[info] applying patch:",p.name)
    subprocess.run(["git","apply","--index","--reject",str(p)], check=True)
  return True
def apply_proposals(folder: Path):
  for prop in folder.glob("*-proposal.md"):
    dst = (Path("docs")/prop.name.replace("-proposal","")) if Path("docs").exists() else Path(prop.name.replace("-proposal",""))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(prop, dst)
  for extra in ["release_notes.md","CHANGELOG.md"]:
    src=folder/extra
    if src.exists(): shutil.copy2(src, Path(extra))
def main():
  if len(sys.argv)!=2: print("usage: apply_proposal.py <proposal_folder>"); sys.exit(1)
  folder=Path(sys.argv[1]).resolve()
  if not folder.exists(): print("proposal folder not found:",folder); sys.exit(1)
  verify_manifest(folder)
  used=apply_patches(folder)
  if not used:
    print("[warn] no patches found; replacing with *-proposal.md files")
    apply_proposals(folder)
  root = Path("docs") if Path("docs").exists() else Path(".")
  with open("MANIFEST.sha256","w",encoding="utf-8") as mf:
    for p in sorted(root.glob("*.md")):
      mf.write(f"{sha256(p)}  {p}\n")
if __name__=="__main__": main()
