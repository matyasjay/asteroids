APP_NAME := asteroids
PY := uv run python
PYINSTALLER := uv run --with pyinstaller pyinstaller
SPEC := $(APP_NAME).spec
ICON_SRC := sprites/ship.png
ICON_PNG := build/app-icon.png
ICON_ICNS := build/app-icon.icns
ICONSET_DIR := build/app.iconset

.PHONY: help sync run test build build-icon open clean distclean

help:
	@echo "Targets:"
	@echo "  make sync      Install/update dependencies via uv"
	@echo "  make run       Run the game from source"
	@echo "  make test      Run test suite (pytest)"
	@echo "  make build-icon Generate macOS app icon (.icns) from sprites/ship.png"
	@echo "  make build     Build macOS app bundle with PyInstaller"
	@echo "  make open      Open built app bundle"
	@echo "  make clean     Remove build artifacts"
	@echo "  make distclean Clean artifacts and Python caches"

sync:
	uv sync

run:
	$(PY) main.py

test:
	uv run --group dev pytest

build-icon:
	@mkdir -p build $(ICONSET_DIR)
	$(PY) -c 'from PIL import Image; src = Image.open("$(ICON_SRC)").convert("RGBA"); size = max(src.width, src.height); canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0)); canvas.paste(src, ((size - src.width) // 2, (size - src.height) // 2)); canvas = canvas.resize((1024, 1024), Image.Resampling.LANCZOS); canvas.save("$(ICON_PNG)")'
	$(PY) -c 'from PIL import Image; base = Image.open("$(ICON_PNG)").convert("RGBA"); sizes = [16, 32, 128, 256, 512]; [base.resize((s, s), Image.Resampling.LANCZOS).save("$(ICONSET_DIR)/icon_{}x{}.png".format(s, s)) or base.resize((s*2, s*2), Image.Resampling.LANCZOS).save("$(ICONSET_DIR)/icon_{}x{}@2x.png".format(s, s)) for s in sizes]'
	iconutil -c icns $(ICONSET_DIR) -o $(ICON_ICNS)

build: build-icon
	$(PYINSTALLER) --noconfirm --clean --windowed \
		--name $(APP_NAME) \
		--icon $(ICON_ICNS) \
		main.py \
		--add-data "images:images" \
		--add-data "sprites:sprites"

open:
	open dist/$(APP_NAME).app

clean:
	rm -rf build dist $(SPEC)

distclean: clean
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
