.SILENT:

GIMP_BIN ?= /Applications/GIMP.app/Contents/MacOS/gimp
UPSCALE_BIN ?= /Applications/Upscayl.app/Contents/Resources/bin/upscayl-bin
UPSCALE_MODELS_DIR ?= /Applications/Upscayl.app/Contents/Resources/models
MAGICK_BIN ?= magick
RCLONE_BIN ?= rclone

RAW_DIR = $(col_dir)/01_canva_raw
UPSCALED_DIR = $(col_dir)/02_upscaled
FINAL_DIR = $(col_dir)/03_final_png

upscale:
	@echo "⚙️ Upscaling de $(file_raw)..."
	@mkdir -p "$(UPSCALED_DIR)"
	@"$(UPSCALE_BIN)" \
		-i "$(RAW_DIR)/$(file_raw)" \
		-o "$(UPSCALED_DIR)/$(file_png)" \
		-s 2 \
		-m "$(UPSCALE_MODELS_DIR)" \
		-n upscayl-standard-4x \
		-f png

finalize:
	@echo "🧱 Génération du PNG final 4800x4800 pour $(file_png)..."
	@mkdir -p "$(FINAL_DIR)"
	@"$(MAGICK_BIN)" \
		"$(UPSCALED_DIR)/$(file_png)" \
		-density 300 \
		-units PixelsPerInch \
		-gravity center \
		-background transparent \
		-extent 4800x4800 \
		"$(FINAL_DIR)/$(file_png)"

edit:
	@echo "🎨 Ouverture dans GIMP de $(file_png) depuis 03_final_png..."
	@"$(GIMP_BIN)" "$(FINAL_DIR)/$(file_png)"

sync:
	@echo "☁️ Upload de $(file_png) vers Google Drive..."
	@"$(RCLONE_BIN)" copy \
		"$(FINAL_DIR)/$(file_png)" \
		"gdrive:/ZONE21/03_BRANDS/BR-21-WEAR/01_OFFER_CATALOG/$(col)/04_POD/03_final_png"
