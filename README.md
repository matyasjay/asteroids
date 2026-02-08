![asteroids](./images/logo.png)

A pet project based on the incredible Asteroids (1979) retro space-game.

## Project Structure

```text
game/
  config/     # Game constants and tuning knobs
  core/       # Shared base types (e.g. CircleShape)
  entities/   # Player, asteroids, shots
  systems/    # Spawners and game systems
  render/     # Texture/sprite helpers
  utils/      # Logging and diagnostics
main.py       # Entry point
sprites/      # Art assets
```

## Extension

- [ ] Add a scoring system
- [ ] Implement multiple lives and respawning
- [x] Add an explosion effect for the asteroids
- [x] Add acceleration to the player movement
- [x] Make the objects wrap around the screen instead of disappearing
- [x] Add a background image
- [ ] Create different weapon types
- [x] Make the asteroids lumpy instead of perfectly round
- [ ] Make the ship have a triangular hit box instead of a circular one
- [ ] Add a shield power-up
- [ ] Add a speed power-up
- [ ] Add bombs that can be dropped
