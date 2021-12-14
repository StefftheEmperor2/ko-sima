addon:
	if [ -f service.ko-sima.zip ]; then rm service.ko-sima.zip; fi
	rm -rf ./dist/service.ko-sima
	mkdir ./dist/service.ko-sima
	rsync -r --exclude '.git' \
	--exclude=".idea" \
	--exclude=".gitignore" \
	--exclude=".gitmodules" \
	--exclude="dist" \
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
	. \
	./dist/service.ko-sima/
	cd ./dist \
	&& zip -9 -r service.ko-sima.zip ./service.ko-sima \
	&& cd ..



