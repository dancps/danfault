# Spotify command examples

Sample output produced by the `spoti` CLI (see [../../docs/spoti.md](../../docs/spoti.md)).

- **`corremo.json`** — a playlist export generated with:

  ```bash
  spoti playlist-export "corremo" --output examples/spotify/corremo.json
  ```

  It is committed as a reference for the shape of the export (playlist metadata +
  per-track fields). It is sample data, not something the tool reads.
