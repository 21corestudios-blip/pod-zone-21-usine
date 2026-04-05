.SILENT:
.PHONY: upscale finalize edit sync

# Variables par défaut, écrasables via variables d'environnement ou arguments CLI
GIMP_BIN ?= gimp
UPSCALE_BIN ?= upscayl-bin
UPSCALE_MODELS_DIR ?= models
MAGICK_BIN ?= magick
RCLONE_BIN ?= rclone

RAW_DIR_NAME ?= 01_canva_raw
UPSCALED_DIR_NAME ?= 02_upscaled
FINAL_DIR_NAME ?= 03_final_png

DRIVE_REMOTE_PATH ?= gdrive:/ZONE21/03_BRANDS/BR-21-WEAR/01_OFFER_CATALOG

RAW_DIR = $(col_dir)/$(RAW_DIR_NAME)
UPSCALED_DIR = $(col_dir)/$(UPSCALED_DIR_NAME)
FINAL_DIR = $(col_dir)/$(FINAL_DIR_NAME)

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
	@echo "🖼️ Génération du PNG final 4800x4800 pour $(file_png)..."
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
	@echo "🎨 Ouverture dans GIMP de $(file_png) depuis $(FINAL_DIR_NAME)..."
	@"$(GIMP_BIN)" "$(FINAL_DIR)/$(file_png)"

sync:
	@echo "☁️ Upload de $(file_png) vers Google Drive..."
	@"$(RCLONE_BIN)" copy \
		"$(FINAL_DIR)/$(file_png)" \
		"$(DRIVE_REMOTE_PATH)/$(col)/04_POD/$(FINAL_DIR_NAME)"
