addon:
	if [ -f ko_sima.zip ]; then rm ko_sima.zip; fi
	zip -9 -r ko_sima.zip . \
	--exclude=".git*" \
	--exclude=".idea*" \
	--exclude="README.md" \
	--exclude="Makefile" \
	--exclude="resources/lib/mpd-sima/data*" \
	--exclude="resources/lib/mpd-sima/tests*" \
	--exclude="Readme.rst" \
	--exclude="*__pycache__*" \
	--exclude="resources/lib/mpd-sima/doc*" \
	--exclude="resources/lib/mpd-sima/INSTALL" \
	--exclude="resources/lib/mpd-sima/README.rst" \
	--exclude="resources/lib/mpd-sima/MANIFEST.in" \
	--exclude="resources/lib/mpd-sima/.git" \
	--exclude="resources/lib/mpd-sima/.gitlab*" \
	--exclude="resources/lib/mpd-sima/.gitlab-ci.yml" \
	--exclude="resources/lib/mpd-sima/setup.py" \
	--exclude="resources/lib/mpd-sima/setup.cfg" \


