# CHANGELOG

## v0.2.1 (2026-08-26)

### Bug fixes

* fix: fix for CI/CD issue ([`b835e64`](https://github.com/BAMresearch/McSAS3GUI/commit/b835e647c868a89761ac6576f3d77576a3473715))

* fix: clear stale prefab file selections when switching examples ([`c8e2529`](https://github.com/BAMresearch/McSAS3GUI/commit/c8e2529960507ca19ba46b59ea3b436c0fd29670))

### Unknown Scope

* Same behaviour implemented for the histogramming tab. ([`f244087`](https://github.com/BAMresearch/McSAS3GUI/commit/f24408755addf9b4b36048354d99e6f4bab16585))

* ensuring previous examples are removed from the optimization tab when another example is chosen ([`eda6924`](https://github.com/BAMresearch/McSAS3GUI/commit/eda69246996e0fb511149ef1851d290fb166c1bb))

* doc: mentioning the structure factor applied to the form factor in the Round Robin dataset 3 example ([`1d70ff1`](https://github.com/BAMresearch/McSAS3GUI/commit/1d70ff1b53381b8bcd42b3835ebdc79a76c2f75c))

## v0.2.0 (2026-08-25)

### Bug fixes

* fix: ruff ([`9eb7bd1`](https://github.com/BAMresearch/McSAS3GUI/commit/9eb7bd1a683c94a49a5f570cbfcf13192f7cd0b2))

* fix: do not restrict the PyQT version (was only necessary for old linux) ([`771be52`](https://github.com/BAMresearch/McSAS3GUI/commit/771be527fdf41aa1942fad88053352ccb8b76c87))

* fix: ruff fix ([`04b2ec3`](https://github.com/BAMresearch/McSAS3GUI/commit/04b2ec34db03c8fabf30da3ed5beabac99689b8e))

* fix: improved dependencies for the current RHEL-based linuxes. May need to be revisited later. ([`045e9ad`](https://github.com/BAMresearch/McSAS3GUI/commit/045e9ad2c64f819e7e49f86fb3927edd5800a22a))

* fix: updates for notarization ([`4005ccd`](https://github.com/BAMresearch/McSAS3GUI/commit/4005ccd2f88785a88370c5267f3b5018e9c1e451))

* fix: adjusting CI so we can run with the in_depth_upgrades branch of McSAS3 ([`0ec6b15`](https://github.com/BAMresearch/McSAS3GUI/commit/0ec6b15dd3d4c23b9800ab37abaa6caf7040cc14))

### Continuous integration

* ci: de-duplicate macOS codesign by realpath and reduce log noise ([`9adc2fe`](https://github.com/BAMresearch/McSAS3GUI/commit/9adc2fe6a3d07566a9fdc04521a23dbe58cdbbc8))

* ci: de-duplicate macOS codesign by realpath and reduce log noise ([`f9e0193`](https://github.com/BAMresearch/McSAS3GUI/commit/f9e0193cc5f60ef5eb8e890964cf42cc978f7e42))

* ci: de-duplicate macOS codesign by realpath and reduce log noise ([`29d6955`](https://github.com/BAMresearch/McSAS3GUI/commit/29d695566a471ddd968aea536d047540d0d5ac89))

* ci: de-duplicate macOS codesign by realpath and reduce log noise ([`5c219d2`](https://github.com/BAMresearch/McSAS3GUI/commit/5c219d265caf6e342e2c8d196e57318e01d41d59))

* ci: de-duplicate macOS codesign by realpath and reduce log noise ([`b144e01`](https://github.com/BAMresearch/McSAS3GUI/commit/b144e01311d73af8b6f2ef6064c3e0254ba00a84))

* ci: handle non-canonical macOS framework signing in release workflow ([`63a0cf9`](https://github.com/BAMresearch/McSAS3GUI/commit/63a0cf9563d29a6036d2231f8b01d3e7fb2ff4fe))

* ci: skip direct file signing inside macOS bundles ([`3819d88`](https://github.com/BAMresearch/McSAS3GUI/commit/3819d885954c7318be708ea0ef79667c979691f4))

* ci: fix macOS codesign ordering in standalone release workflow ([`b9b9942`](https://github.com/BAMresearch/McSAS3GUI/commit/b9b99420d4c0bbffaf19d237312db4c12a5d0b5c))

* ci: add standalone release workflow ([`efdfc21`](https://github.com/BAMresearch/McSAS3GUI/commit/efdfc218231d25a6bf59c7c55dbdcb095cd52bf2))

* **PyPI**: fix pypi url, switch to actions/checkout@v5 ([`ea8998e`](https://github.com/BAMresearch/McSAS3GUI/commit/ea8998e5eeaf55330eaa7ac466f62759a4fa5930))

* **PyPI**: copier template update other places to pypi.org as well ([`5b00873`](https://github.com/BAMresearch/McSAS3GUI/commit/5b0087381339751385d856de725163b21dfd4d79))

* **PyPI**: move from test.pypi.org to pypi.org ([`97d72f2`](https://github.com/BAMresearch/McSAS3GUI/commit/97d72f2acf0fb21691cdb5c98b47d205122b9b5a))

### Enh

* enh: added python3.14 to tox tests ([`71f9689`](https://github.com/BAMresearch/McSAS3GUI/commit/71f96895d5d079071b82854bf462b0bb0a7efa12))

* enh: build standalone versions for three plarforms ([`7fb84b8`](https://github.com/BAMresearch/McSAS3GUI/commit/7fb84b8442c7167b6207b7fcd2529d156926a77a))

### Testing

* **Style**: checks moved to early tests stage ([`9f722d5`](https://github.com/BAMresearch/McSAS3GUI/commit/9f722d556dbec236eb583d8c8dfec5fa1e4d724f))

### Unknown Scope

* Fix for Linux build ([`08b72ec`](https://github.com/BAMresearch/McSAS3GUI/commit/08b72ec7ac19f208072af1ed31ee20dfc33b1160))

* track main branch of McSAS, no longer in_depth_upgrades ([`ffaccef`](https://github.com/BAMresearch/McSAS3GUI/commit/ffaccef65efaea882fe8e7afc775c49c5cdd1fd0))

* Bump the GLIBC version requirement of Linux to a more modern version to avoid limiting ourselves to old PyQT versions ([`e6f812d`](https://github.com/BAMresearch/McSAS3GUI/commit/e6f812d815aa0f5999a5ab102b579feacfa001ea))

* simulated data now will use automatic porod slope determination for extrapolation ([`bad6e19`](https://github.com/BAMresearch/McSAS3GUI/commit/bad6e199cb283702a9d9988359d10918218d606f))

* simulated data now will use automatic porod slope determination for extrapolation ([`0956ead`](https://github.com/BAMresearch/McSAS3GUI/commit/0956ead475ad342eff34272fdbafac429a7056e5))

* modified README to add a uv installation path ([`28b839f`](https://github.com/BAMresearch/McSAS3GUI/commit/28b839f4b837549cc4bdec52e290329422fcdd75))

* documentation and default configuration updates ([`edd3c7f`](https://github.com/BAMresearch/McSAS3GUI/commit/edd3c7fd53300ae26ae7dc957414e13a9e49a803))

* doc: Updated build release documentation ([`9685a5d`](https://github.com/BAMresearch/McSAS3GUI/commit/9685a5d979443010546e1cbca0c51455791dcf3c))

* Fixes to binary build scripts ([`f623285`](https://github.com/BAMresearch/McSAS3GUI/commit/f62328591007db16630235cc16081ecef263085e))

* added notarization ([`fbc0ba6`](https://github.com/BAMresearch/McSAS3GUI/commit/fbc0ba650027fbe94fa27543d06d19647abc55ed))

* trying a different approach ([`62c34e8`](https://github.com/BAMresearch/McSAS3GUI/commit/62c34e8e09dba8c2b2c70a46f041fd38a0a6d108))

* patching workflows ([`88d28cb`](https://github.com/BAMresearch/McSAS3GUI/commit/88d28cbccb2b285197ac9fe92f1fe09c065ed9d5))

* fix for seed issue ([`d31867a`](https://github.com/BAMresearch/McSAS3GUI/commit/d31867a52f0544ac9efb6d53670dc63c5e342b15))

* setting up for code signing for mac os x in CI ([`c7a4043`](https://github.com/BAMresearch/McSAS3GUI/commit/c7a404373d44dc83f879fc6dab2b6396a651199a))

* fix build paths ([`c14d483`](https://github.com/BAMresearch/McSAS3GUI/commit/c14d48340e96d77bcc51b2b8fdd13bb09e33b647))

* yet another test fix. ([`e50848b`](https://github.com/BAMresearch/McSAS3GUI/commit/e50848b97bbef63e6c28c26eb76bddb12abba17b))

* fix to imports, shifting python to match modacor reqs. ([`9baed9c`](https://github.com/BAMresearch/McSAS3GUI/commit/9baed9c71b1d80e2572afa544b959981482bced1))

* addressing small usability issues. ([`9fad697`](https://github.com/BAMresearch/McSAS3GUI/commit/9fad697d27022d942a628bcad050e01aa2b9b93d))

* fixing small documentation issue ([`25065ea`](https://github.com/BAMresearch/McSAS3GUI/commit/25065eab4c566056e8ba7897d773b89d8afc9634))

* bugfixes in compiled build ([`5d52e4b`](https://github.com/BAMresearch/McSAS3GUI/commit/5d52e4bc35ba0806935900525ce213edc1d586e5))

* bugfix ([`f3c1729`](https://github.com/BAMresearch/McSAS3GUI/commit/f3c1729e677553772d24837f280425b1676db30e))

* compiled McSAS3GUI ([`2a3b138`](https://github.com/BAMresearch/McSAS3GUI/commit/2a3b13879151126bd8cd10d7a0ac8a796d303543))

* aux windows close when main closes ([`6bf68db`](https://github.com/BAMresearch/McSAS3GUI/commit/6bf68db9352461dbda1c6947064633ef25aeab85))

* bugfix ([`524db9f`](https://github.com/BAMresearch/McSAS3GUI/commit/524db9f550e2b85fb3b70a667a3b32201aa5c995))

* documentation generation ([`fc0d7d0`](https://github.com/BAMresearch/McSAS3GUI/commit/fc0d7d091bafc2405735101c98302b8f5731cf85))

* typing/docstrings added ([`26c1d4e`](https://github.com/BAMresearch/McSAS3GUI/commit/26c1d4e567151eb884189d9efbcff27e46b47a31))

* more cleanip, moving on to docs next ([`7058012`](https://github.com/BAMresearch/McSAS3GUI/commit/7058012fff60975a90298f742cf1da08ddae18a5))

* more cleanup ([`3f48b72`](https://github.com/BAMresearch/McSAS3GUI/commit/3f48b7219b4cae3394751ad18df6b019735dd0eb))

* next cleanup step ([`b36da89`](https://github.com/BAMresearch/McSAS3GUI/commit/b36da896dffebf250a93f03c7d326482f0581015))

* more cleanup ([`f63560e`](https://github.com/BAMresearch/McSAS3GUI/commit/f63560e97ecce760782563171c43150da001c553))

* another cleanup sweep ([`2051dfb`](https://github.com/BAMresearch/McSAS3GUI/commit/2051dfbc1d8f03167911b13644ae87c4156a03c0))

* continuing cleanup ([`a7ff42f`](https://github.com/BAMresearch/McSAS3GUI/commit/a7ff42f564926bdd2eb17eca49ec462d18d394b9))

* cleanup pass and tests ([`de4dda8`](https://github.com/BAMresearch/McSAS3GUI/commit/de4dda8a8bca26175d6e6e72dbf68def97ab78d2))

* initial cleanup pass on McSAS3GUI ([`95dd184`](https://github.com/BAMresearch/McSAS3GUI/commit/95dd1840bf8c91adeb255b0865e2a9e93c43e25d))

* adjusting the test configuration ([`82c2c20`](https://github.com/BAMresearch/McSAS3GUI/commit/82c2c2035ac0304756ea59c39962c85b100343c0))

* stop button on test run too. ([`cdd39cf`](https://github.com/BAMresearch/McSAS3GUI/commit/cdd39cfe14ffb221eb52aa500facbd97b04a5501))

* implement stop functionality ([`1fc1bba`](https://github.com/BAMresearch/McSAS3GUI/commit/1fc1bba27b2efdcc66d1317dbd0762ea1a7464b0))

* adjusted ignores and added missing info ([`f6f954b`](https://github.com/BAMresearch/McSAS3GUI/commit/f6f954b66cda5228c9cc45e9418b292ac87bf554))

* adjust gitignore ([`f598571`](https://github.com/BAMresearch/McSAS3GUI/commit/f5985714b52afc3849165eae9b4d6c4f9c26fed5))

* adapting to the new API of McSAS3 with ProcessingData ([`d3243ac`](https://github.com/BAMresearch/McSAS3GUI/commit/d3243ac9f87309e369c81094d39d25c121637c3f))

* basic formatting and project git hooks, we'll pick this up after we're done with McSAS3 upgrades. ([`192e829`](https://github.com/BAMresearch/McSAS3GUI/commit/192e829b48616ee99628805043eacbc73e9dd0c5))

## v0.1.6 (2025-09-05)

### Bug fixes

* **RunSettingsTab**: show helpful info for simulation model ([`2b72793`](https://github.com/BAMresearch/McSAS3GUI/commit/2b72793a4054c395422ce39f028949983200af50))

### Unknown Scope

* enhancement(PreFab): Added an example using simulated base model data. ([`1948f8d`](https://github.com/BAMresearch/McSAS3GUI/commit/1948f8d3a2660046a19db5abf1f825fe150cbfd1))

## v0.1.5 (2025-09-05)

### Bug fixes

* **Histogramming**: actually use new input/ouput paths given to hist_run_tab ([`51398b2`](https://github.com/BAMresearch/McSAS3GUI/commit/51398b21ff5e622f8ad5aa5dd9336b672c536922))

### Unknown Scope

* Update on logo ([`c82daec`](https://github.com/BAMresearch/McSAS3GUI/commit/c82daecf85c1d0f08c8a7b9e2feacfc172bc0f4b))

## v0.1.4 (2025-08-15)

### Bug fixes

* **HistogramSettingsTab**: set expected output file, do not use (not working) paths from *prefab* ([`a0c59ab`](https://github.com/BAMresearch/McSAS3GUI/commit/a0c59ab39afe74495defb41923f5469b4fed7d4a))

* **GettingStartedTab**: test aginst the tab which is to be modified ([`0c35ce0`](https://github.com/BAMresearch/McSAS3GUI/commit/0c35ce0fc720abf608df3c4d388fe0f3320216d0))

### Code style

* **General**: formatting ([`2d97002`](https://github.com/BAMresearch/McSAS3GUI/commit/2d97002adcd9460b75a1941c5beb78936bf4ac52))

## v0.1.3 (2025-08-14)

### Bug fixes

* **PreFab**: output files from testdata written to temp directory as well ([`0fd0442`](https://github.com/BAMresearch/McSAS3GUI/commit/0fd044266f0c10ea9fca3cf297af7982a643965a))

* **RunSettingsTab**: use the same temp dir in run_test_optimization() ([`7ac2399`](https://github.com/BAMresearch/McSAS3GUI/commit/7ac2399c6d52fa046c12120d55c737436958dbb5))

* **GettingStartedTab & Logging**: create a proper temp dir out-of-source for log files and intermediate configs ([`a4b5bdf`](https://github.com/BAMresearch/McSAS3GUI/commit/a4b5bdfe6116703fe8859c380fc4cca06b53d219))

* **DataLoadingTab**: csvargs is expected as dict in McSAS ([`209dc62`](https://github.com/BAMresearch/McSAS3GUI/commit/209dc62fc5ef5a9b84b304fdea35e7873f893c65))

* **Configurations Examples**: moved to src dir since they need to be installed along ([`e75c5a6`](https://github.com/BAMresearch/McSAS3GUI/commit/e75c5a6639dace8885961bbe0e4c510b7f45b326))

* **Project**: remove redundant dependencies implied by mcsas3 ([`2e550ef`](https://github.com/BAMresearch/McSAS3GUI/commit/2e550ef646360d91be1a3115f1b4f6a30e873ea6))

### Continuous integration

* **Publish**: show verbose messages in case of error ([`35c0bed`](https://github.com/BAMresearch/McSAS3GUI/commit/35c0bedd1df81a22a44748752ceefb3b6ab47087))

* **Tests**: testing Windows ([`5ff1ebc`](https://github.com/BAMresearch/McSAS3GUI/commit/5ff1ebc1d98f9713adca8ea4a5b1c63d3caf7b32))

* **Publish**: pypi url needs /legacy/ suffix ([`15121e8`](https://github.com/BAMresearch/McSAS3GUI/commit/15121e8f5dce114220e0d00b5787769e6ca9703f))

* **Publish**: use test.pypi.org ([`505c64a`](https://github.com/BAMresearch/McSAS3GUI/commit/505c64aa07fc683f990b9b65217edcddd0ed5c6a))

## v0.1.2 (2025-08-13)

### Bug fixes

* **Project**: McSAS3 dependency available on PyPI now ([`cf280f8`](https://github.com/BAMresearch/McSAS3GUI/commit/cf280f89e12b583ac9ce267d0912645a8cdb914c))

### Code style

* **General**: formatting improved ([`9159f96`](https://github.com/BAMresearch/McSAS3GUI/commit/9159f968c560aebdd19b741570a2dff1c0b54e3f))

### Continuous integration

* **Release**: debug job ([`82c1952`](https://github.com/BAMresearch/McSAS3GUI/commit/82c195284a4eb405f725d4b83ed1438d4744432c))

* **Docs**: update package DB here as well ([`0496071`](https://github.com/BAMresearch/McSAS3GUI/commit/04960719d998362802bdb02735cf2e403288e655))

* **Tests**: before installing sys packages, update package DB, to avoid outdated lists ([`e00a085`](https://github.com/BAMresearch/McSAS3GUI/commit/e00a085cac8194b0d44eee98624ef4a851f503be))

* **Tests**: try installing PyQt6 system-wide to get all required binary dependencies ([`be3e5f5`](https://github.com/BAMresearch/McSAS3GUI/commit/be3e5f5d451f0225831cee7d2b1a9a48cda9295c))

* **Tests**: typo installing additional system packages required by PyQt6 ([`909c208`](https://github.com/BAMresearch/McSAS3GUI/commit/909c2084939253d4809b25f6c14593862e7b7918))

* **Tests**: additional system packages required by PyQt6 ([`9584c29`](https://github.com/BAMresearch/McSAS3GUI/commit/9584c296dc85826ce99b39dc9be157782b19dc70))

### Unknown Scope

* Revert "ci(Release): debug job" ([`e3fd4ed`](https://github.com/BAMresearch/McSAS3GUI/commit/e3fd4eddf990a05d2ca6845615cafbcac426158d))

* tests(Utils): remove unused code which causes import errors ([`c407196`](https://github.com/BAMresearch/McSAS3GUI/commit/c40719635f67c603d7c310ed6224b8c5a59258d1))

## v0.1.1 (2025-08-12)

### Unknown Scope

* 0.1.1 ([`29a34cc`](https://github.com/BAMresearch/McSAS3GUI/commit/29a34cc454885061f918336042de2ab032ac5afa))

* Last example: RR dataset 3 ([`210889e`](https://github.com/BAMresearch/McSAS3GUI/commit/210889e1ac642cfa78eb3059d7fdd24db760f056))

* will work on 3.10 as well. ([`4ed299e`](https://github.com/BAMresearch/McSAS3GUI/commit/4ed299edb749589b7a340f0b13af91e606351350))

* modern numpy now works as well, removing restriction on python 3.13 ([`86cf44b`](https://github.com/BAMresearch/McSAS3GUI/commit/86cf44b0e8dbf16a45203a2935eb6da1b93c2e23))

* Extra explanation ([`400c602`](https://github.com/BAMresearch/McSAS3GUI/commit/400c602cdc51987e59cc574bc3f74d299184d743))

* Updates to the examples ([`bb33ec8`](https://github.com/BAMresearch/McSAS3GUI/commit/bb33ec86c63a5970f41d18fe73edadba9b766c0b))

* Adjustment to the advanced nexus demo (highlighting logRandom), and addition of the round robin 1 demo ([`6fa5d84`](https://github.com/BAMresearch/McSAS3GUI/commit/6fa5d84cc3a746a8b1371b2321493d568d11a756))

* adding logo ([`49e14da`](https://github.com/BAMresearch/McSAS3GUI/commit/49e14dae7fc0f70679a69371027d6da7d9555a7b))

* improved structure of eventFilter. Still allows internal drag and drops though. ([`d9e0025`](https://github.com/BAMresearch/McSAS3GUI/commit/d9e0025c2d72588bffb4cc25c2856f762bb7a6c5))

* Fixing table highlight color ([`02a7232`](https://github.com/BAMresearch/McSAS3GUI/commit/02a7232d5d8be148c73b07d1737ebbdcba2af330))

* Drag and drop fix for the file table widgets. This was hard. ([`28036da`](https://github.com/BAMresearch/McSAS3GUI/commit/28036dad7596bac08abcec02c47ffa3781ec63d2))

* Add drag-and-drop support for files into the tables. ([`02b8009`](https://github.com/BAMresearch/McSAS3GUI/commit/02b80098cca0be226a478c901026f942bf8d287b))

* last one ([`3014af0`](https://github.com/BAMresearch/McSAS3GUI/commit/3014af06cded75b2d23dcdf46f80196e10eb95d4))

* Ok, windows is a pain in the butt. ([`800965f`](https://github.com/BAMresearch/McSAS3GUI/commit/800965ff2a59fafb97c1ad0717bbc4c01f7adef7))

* Applying some style to override Window's dark defaults. ([`20572e9`](https://github.com/BAMresearch/McSAS3GUI/commit/20572e91b5470c372327a29494e4ad6d3aadcbda))

* Stopped messing around with fonts as they're not consistent cross-platform. ([`0ba0b09`](https://github.com/BAMresearch/McSAS3GUI/commit/0ba0b0912222ce30bd0db7f9c793b5751fe48033))

* minifix. ([`3281589`](https://github.com/BAMresearch/McSAS3GUI/commit/3281589709ba3c11446fc502619743515a5211d3))

* Changing debug levels ([`0f2cd55`](https://github.com/BAMresearch/McSAS3GUI/commit/0f2cd55ad1111717052f5aee541aecdf07663604))

* Improving the text on the three examples. ([`166ee4f`](https://github.com/BAMresearch/McSAS3GUI/commit/166ee4f45d8fe6e2d60cbc3c218c96cda53e13f9))

* New nexus example, and an update to the configuration files ([`9d67def`](https://github.com/BAMresearch/McSAS3GUI/commit/9d67def732be0f613859e1851e989e44aa09b558))

* Update order and text. ([`d049a36`](https://github.com/BAMresearch/McSAS3GUI/commit/d049a3602474c867997eed693efeb93bc233547f))

* showing the test histogram PDF, even on Windows ([`2b7119f`](https://github.com/BAMresearch/McSAS3GUI/commit/2b7119fd12bb8a4ae32f577a77bb53b052059a21))

* Trying to get the PDF to show on Windows. ([`0cd3889`](https://github.com/BAMresearch/McSAS3GUI/commit/0cd38899a94ada933fe7cc6591d974efe9df7256))

* Bug fixes for windows ([`1d21d51`](https://github.com/BAMresearch/McSAS3GUI/commit/1d21d518ad5197c4608f2a263272b21b88b4a3b8))

* making sure we can plot the test histogram also in windows ([`4fa9b37`](https://github.com/BAMresearch/McSAS3GUI/commit/4fa9b371e365a1aad851368e7a12f2b3150b389b))

* minifix ([`519335e`](https://github.com/BAMresearch/McSAS3GUI/commit/519335e04fd9cc9145d002ed3fbf45a8aca1077a))

* Can load prefabricated examples from a single yaml ([`6dcdc12`](https://github.com/BAMresearch/McSAS3GUI/commit/6dcdc12768557f790b7078ac90d321611f911d89))

* Removing too challenging nexus data from the test data. ([`6e6a379`](https://github.com/BAMresearch/McSAS3GUI/commit/6e6a379b80a8307ec6277659f1e507f233861765))

* updating getting started. ([`e0a138e`](https://github.com/BAMresearch/McSAS3GUI/commit/e0a138eddb0c639d370238dcba0e9c639c56728b))

* correcting file extension of processed files to .hdf5 ([`606d5d1`](https://github.com/BAMresearch/McSAS3GUI/commit/606d5d1b82f408fd1fa3347e190b43da52faef36))

* fixing a path issue on windows ([`d6c6783`](https://github.com/BAMresearch/McSAS3GUI/commit/d6c6783a657595214e8ce25e047569bc0d60e8b5))

* prevent breaking on windows with empty model name ([`75c0cb3`](https://github.com/BAMresearch/McSAS3GUI/commit/75c0cb3b661baba02e8e261139d4cf1e4a23a76a))

* Ensure that the default configurations are loaded from the correct path ([`b87a922`](https://github.com/BAMresearch/McSAS3GUI/commit/b87a922e98ffd57b385f09b749fcc3cda86da534))

* fixed annoying window repositioning issue ([`5446eaf`](https://github.com/BAMresearch/McSAS3GUI/commit/5446eaf405a5c2daa1612d943571c7752a4215d2))

* Fixing small usability issue - launch with python -m mcsas3gui ([`7b56ae6`](https://github.com/BAMresearch/McSAS3GUI/commit/7b56ae637fd53f2935e6d4f481544d8353ca1b60))

* Change the way mcsas3 is launched to avoid command-line scripts. ([`008f094`](https://github.com/BAMresearch/McSAS3GUI/commit/008f094812f386df1b180f762d2fd63287d4a60e))

* enforcing posix paths on CLI ([`2f3c3ee`](https://github.com/BAMresearch/McSAS3GUI/commit/2f3c3ee15874d4ba5e2bd6e917b2080a2450f24e))

* Updated pyproject fixing bug ([`a44d922`](https://github.com/BAMresearch/McSAS3GUI/commit/a44d9227daf0a341a3b0cdc0e548c6282c08ecf7))

* small update ([`02b6018`](https://github.com/BAMresearch/McSAS3GUI/commit/02b6018ed1dbaea46e3e84daa49801a880d909c8))

* pyinstaller --name McSAS3GUI --windowed src/mcsas3gui/main.py # not yet fully functional executable ([`7986876`](https://github.com/BAMresearch/McSAS3GUI/commit/7986876ac6c8822689e6d7468c9acd4b3e69ed32))

* updated pyproject towards build ([`34128cd`](https://github.com/BAMresearch/McSAS3GUI/commit/34128cdb70ffc23e2fc037c3c1daacd920e08c24))

* reorganisation to enable pip installability, resulting in command-line m3gui ([`63a0795`](https://github.com/BAMresearch/McSAS3GUI/commit/63a0795a10fffeb9d3e6a974827be0ac735233e2))

* connecting signals to set saved config files in the optimization and histogramming tabs ([`411d120`](https://github.com/BAMresearch/McSAS3GUI/commit/411d120fd89b2fa388aa48b624740c451a9f3af7))

* Updating pulldown menus on save ([`ab2a492`](https://github.com/BAMresearch/McSAS3GUI/commit/ab2a492725630fc731b6d89d9023f3ae392bd05c))

* A readme and a license ([`477e819`](https://github.com/BAMresearch/McSAS3GUI/commit/477e819ee5886bdbfaf542999fd06d90819d6907))

* updated requirements to remove particular mcsas3 commit ([`3654674`](https://github.com/BAMresearch/McSAS3GUI/commit/36546740980b9a533f608d66e7331358c79d2a09))

* handling of IEmin in data settings tab ([`16a2b55`](https://github.com/BAMresearch/McSAS3GUI/commit/16a2b558fae752795bc38a1975ac37dba7ad4815))

* Minor edits for readability ([`5aa460b`](https://github.com/BAMresearch/McSAS3GUI/commit/5aa460b50ac60dc6edc0fda4921d716aed914de4))

* Adjusting the yaml display and saving with a custom dumper ([`967be91`](https://github.com/BAMresearch/McSAS3GUI/commit/967be910dd17abad581f77b4ed083bc012840db5))

* Fleshing out the "Getting Started" helpful bits. ([`e109fd6`](https://github.com/BAMresearch/McSAS3GUI/commit/e109fd65981cd3d3cc77e0e9b36d5a3da5e9aaba))

* Clearer plotting when using omit ([`2d5639e`](https://github.com/BAMresearch/McSAS3GUI/commit/2d5639ebb1ada7d7d59a8214a38ad378e6a2bd4c))

* Test histogram now opens PDF automatically. ([`c815eeb`](https://github.com/BAMresearch/McSAS3GUI/commit/c815eebfb7b6e05a7784fac0301b6df278e69dcf))

* Histogramming works and editor works.. ([`1f9afb0`](https://github.com/BAMresearch/McSAS3GUI/commit/1f9afb0dc07d4f0d03f224b9699d502ea5bf95de))

* fix file extensions ([`48cdc8f`](https://github.com/BAMresearch/McSAS3GUI/commit/48cdc8f9c3040b036cd8c2cc2010378d11dee26a))

* Drag and drop file line entry widgets now all working. ([`7fe3e2d`](https://github.com/BAMresearch/McSAS3GUI/commit/7fe3e2d448cbf5acdfb7f9ea30768df5b2522de8))

* Abstracted the file line selection widget ([`1364400`](https://github.com/BAMresearch/McSAS3GUI/commit/1364400e63ce706e073d16a4e67c3472583fb2ef))

* Adding a reusable file-line selection widget with drag and drop ([`9ef410a`](https://github.com/BAMresearch/McSAS3GUI/commit/9ef410aeb8c9bbd0b7c52cb0df5a91f82ffb886a))

* bug resolved with spaces in filenames. ([`e36b7ee`](https://github.com/BAMresearch/McSAS3GUI/commit/e36b7eeaa27b68980bbe74bd632247e2a7806290))

* Trying to get drag and drop working in the file tabulation widget ([`5dc689c`](https://github.com/BAMresearch/McSAS3GUI/commit/5dc689c22615951ea9a297e10a4ae8bd9d9df9ca))

* Updates... ([`dd65ab4`](https://github.com/BAMresearch/McSAS3GUI/commit/dd65ab4d74057a55b4e644563f537b2b5b650598))

* separated the file selection table for optimization and histogramming ([`90da9e6`](https://github.com/BAMresearch/McSAS3GUI/commit/90da9e6e225080d362cc1c007bc564864a34fe33))

* setting previously used directories for user convenience ([`0731646`](https://github.com/BAMresearch/McSAS3GUI/commit/07316469bc8feeaec549b178be181503614a6b1e))

* cleanup ([`dfbfe61`](https://github.com/BAMresearch/McSAS3GUI/commit/dfbfe610c26aefc5b51cc001c48a3ea3e50c8348))

* editor now functional for multipart yamls (needed for histogramming) ([`1e7f061`](https://github.com/BAMresearch/McSAS3GUI/commit/1e7f061d4d102bfbad42c991e9d273524a14d9bd))

* Getting there.. ([`e9224e1`](https://github.com/BAMresearch/McSAS3GUI/commit/e9224e19dc1794778861d6c4c8f0e9ba4d9a3140))

* updates. ([`2948074`](https://github.com/BAMresearch/McSAS3GUI/commit/2948074e1b3cf6b384e89661ea936dd0ebc2608a))

* Somewhat functional, processes cannot be killed yet, however. ([`8e2a449`](https://github.com/BAMresearch/McSAS3GUI/commit/8e2a449945f2c3eed1ea0a7330451fd5e6e63067))

* Now can run and show a test optimization ([`983f12c`](https://github.com/BAMresearch/McSAS3GUI/commit/983f12c44059e9ae3bfa0dd6081651e29e1354c6))

* Setting up test runs in run_settings tab. ([`30f5033`](https://github.com/BAMresearch/McSAS3GUI/commit/30f50338e9ca8306de518189706b8c93bde24079))

* updating run settings ([`73b8279`](https://github.com/BAMresearch/McSAS3GUI/commit/73b8279f28535de04e7da75036b88c67cc1c0256))

* Updates to data loading, I think it works for now. ([`be9fd17`](https://github.com/BAMresearch/McSAS3GUI/commit/be9fd1775814de9f43494f08e97eb4c9603f2b93))

* upgrades ([`24cae6d`](https://github.com/BAMresearch/McSAS3GUI/commit/24cae6dfff2fd65aaeb4a3872f712a47b9769613))

* working ok now. ([`3b43344`](https://github.com/BAMresearch/McSAS3GUI/commit/3b4334421909c860cd475e39d15984025407eb96))

* data loading tab starting to look like something useful now. ([`8a4e925`](https://github.com/BAMresearch/McSAS3GUI/commit/8a4e925f6d5615f968887bbba41ec9a544d30a7e))

* Now loads and plots ([`0d7dc3c`](https://github.com/BAMresearch/McSAS3GUI/commit/0d7dc3cbda5e39a58c8e673a43f10f50283d02e0))

* minimal change in naming. ([`3859dcd`](https://github.com/BAMresearch/McSAS3GUI/commit/3859dcd1f01f27d0cab3181b52fae126d34a2e18))

* Updated main window naming ([`20b0063`](https://github.com/BAMresearch/McSAS3GUI/commit/20b0063c5cb92ad4090784545f6c61424052e819))

* Drafted the optimization tab contents ([`d3b1e89`](https://github.com/BAMresearch/McSAS3GUI/commit/d3b1e89feb88e1bcbcfddf9ee4da907d7315b83e))

* some additions, but nothing working yet ([`41acbd8`](https://github.com/BAMresearch/McSAS3GUI/commit/41acbd8b07b5ac7b037caa601943db774e51129b))

* sasmodels automatically interpreted ([`b11ae97`](https://github.com/BAMresearch/McSAS3GUI/commit/b11ae9753576468414fccf8ced6f10708aa94e56))

* run config now working with central yaml editor. editor has syntax highlighting and syntax error tooltips. ([`1d02a85`](https://github.com/BAMresearch/McSAS3GUI/commit/1d02a85c4505a4f8a5ebf168b8f7e37c49481a64))

* Centralizing the yaml editor widget ([`8cc2761`](https://github.com/BAMresearch/McSAS3GUI/commit/8cc27612dbebd744f506298368fc3475e1c86a70))

* sort of working ([`0bfbf07`](https://github.com/BAMresearch/McSAS3GUI/commit/0bfbf07bc2780e5cec404b8915434b2996dcde27))

* first commit ([`5fcbc09`](https://github.com/BAMresearch/McSAS3GUI/commit/5fcbc09d9be2d84324c4bbc48caa1d5eee7e77df))
