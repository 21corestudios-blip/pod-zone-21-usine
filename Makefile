.SILENT:
.PHONY: help upscale finalize edit sync

# Variables par défaut, écrasables via variables d'environnement ou arguments CLI
GIMP_BIN ?= gimp
UPSCALE_BIN ?= upscayl-bin
UPSCALE_MODELS_DIR ?= models
MAGICK_BIN ?= magick
RCLONE_BIN ?= rclone

RAW_DIR_NAME ?= 01_canva_raw
UPSCALED_DIR_NAME ?= 02_upscaled
FINAL_DIR_NAME ?= 03_final_png
PUBLISHED_DIR_NAME ?= 04_publies

DRIVE_REMOTE_PATH ?= gdrive:/ZONE21/03_BRANDS/BR-21-WEAR/01_OFFER_CATALOG

RAW_DIR = $(col_dir)/$(RAW_DIR_NAME)
UPSCALED_DIR = $(col_dir)/$(UPSCALED_DIR_NAME)
FINAL_DIR = $(col_dir)/$(FINAL_DIR_NAME)

help:
	echo "Targets disponibles :"
	echo "  make upscale  col=<collection> col_dir=<.../04_POD> file_raw=<source.psd> file_png=<target.png>"
	echo "  make finalize col=<collection> col_dir=<.../04_POD> file_png=<target.png>"
	echo "  make edit     col=<collection> col_dir=<.../04_POD> file_png=<target.png>"
	echo "  make sync     col=<collection> col_dir=<.../04_POD> file_png=<target.png>"

upscale:
	test -n "$(col_dir)" || (echo "❌ col_dir manquant" && exit 1)
	test -n "$(file_raw)" || (echo "❌ file_raw manquant" && exit 1)
	test -n "$(file_png)" || (echo "❌ file_png manquant" && exit 1)
	echo "⚙️ Upscaling de $(file_raw)..."
	mkdir -p "$(UPSCALED_DIR)"
	"$(UPSCALE_BIN)" \
		-i "$(RAW_DIR)/$(file_raw)" \
		-o "$(UPSCALED_DIR)/$(file_png)" \
		-s 2 \
		-m "$(UPSCALE_MODELS_DIR)" \
		-n upscayl-standard-4x \
		-f png

finalize:
	test -n "$(col_dir)" || (echo "❌ col_dir manquant" && exit 1)
	test -n "$(file_png)" || (echo "❌ file_png manquant" && exit 1)
	echo "🖼️ Génération du PNG final 4800x4800 pour $(file_png)..."
	mkdir -p "$(FINAL_DIR)"
	"$(MAGICK_BIN)" \
		"$(UPSCALED_DIR)/$(file_png)" \
		-density 300 \
		-units PixelsPerInch \
		-gravity center \
		-background transparent \
		-extent 4800x4800 \
		"$(FINAL_DIR)/$(file_png)"

edit:
	test -n "$(col_dir)" || (echo "❌ col_dir manquant" && exit 1)
	test -n "$(file_png)" || (echo "❌ file_png manquant" && exit 1)
	echo "🎨 Ouverture dans GIMP de $(file_png) depuis $(FINAL_DIR_NAME)..."
	"$(GIMP_BIN)" "$(FINAL_DIR)/$(file_png)"

sync:
	test -n "$(col_dir)" || (echo "❌ col_dir manquant" && exit 1)
	test -n "$(col)" || (echo "❌ col manquant" && exit 1)
	test -n "$(file_png)" || (echo "❌ file_png manquant" && exit 1)
	echo "☁️ Upload de $(file_png) vers Google Drive..."
	"$(RCLONE_BIN)" copy \
		"$(FINAL_DIR)/$(file_png)" \
		"$(DRIVE_REMOTE_PATH)/$(col)/04_POD/$(FINAL_DIR_NAME)"
