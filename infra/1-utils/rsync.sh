sudo rsync \
  -r \
  --partial \
  --checksum \
  --ignore-errors \
  --info=progress2 \
  --log-file="./2026-02-03_rsync.log" \
  --log-file-format="%t %o %f %l" \
  /Users/enovikov11/ "/Volumes/4TB/2026-02-03/"