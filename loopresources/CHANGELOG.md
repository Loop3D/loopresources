# Changelog

## [0.0.2](https://github.com/Loop3D/loopresources/compare/v0.0.1...v0.0.2) (2025-11-19)


### Bug Fixes

* add code to merge two interval tables: Currently a bit slow ([12d7b02](https://github.com/Loop3D/loopresources/commit/12d7b02377180d7d48647b44ca11b4091d50b235))
* add flag for +ve dips down, convert +ve dips to negative on load ([0da4293](https://github.com/Loop3D/loopresources/commit/0da429367212715cb408f45b5c6e4fc51b82a77d))
* add function to calculate drillhole intersection with implicit function ([24fe408](https://github.com/Loop3D/loopresources/commit/24fe408c869b188c246badacb69c3b46ef99a436))
* add holeid to drillhole implicit function intersection ([b8cab24](https://github.com/Loop3D/loopresources/commit/b8cab2456cdbe21be3c154e7e47c992dd1ce7c7b))
* add intersection value to implicit function intersection calc ([5d7f802](https://github.com/Loop3D/loopresources/commit/5d7f8028c27c8ae389d6c0a44c39cccc47835018))
* add vtk method for database and drillhole. ([c63a25d](https://github.com/Loop3D/loopresources/commit/c63a25d1d0a27526b6afc0a5c0400ae576a38b12))
* adding efficient numpy resampling logic ([91f370a](https://github.com/Loop3D/loopresources/commit/91f370a4f0a5f4f58a7b343b0c9ffa05128c7ea5))
* adding orientation calc from alpha beta ([3deed6e](https://github.com/Loop3D/loopresources/commit/3deed6e9c86bd52b4b9c44ac61afc4ace3ff5259))
* adding pre-commit ([83ed914](https://github.com/Loop3D/loopresources/commit/83ed914aaf37de0929b9516676113e3a277f5fc6))
* allow point/interval tables to be csv paths ([72176fb](https://github.com/Loop3D/loopresources/commit/72176fb342df5d40119c7bd0bf9f00da836850de))
* assign property name directly to vtk object ([27b2093](https://github.com/Loop3D/loopresources/commit/27b209392e90546309380858f9bc9267c830dc26))
* avoid pandas copy warning ([672e965](https://github.com/Loop3D/loopresources/commit/672e9658318d965b0810599c95f1f8e6fda42c8c))
* avoiding overcalling pandas insert ([dcbecfe](https://github.com/Loop3D/loopresources/commit/dcbecfe4745f88def87e328c11b0e8af8cdf796e))
* change alphabetagamma to use dhconfig ([2d84986](https://github.com/Loop3D/loopresources/commit/2d8498603b10f0d37b94d23193e0be400bf75cf3))
* change interval/point mapping to use pandas syntax ([8724b6e](https://github.com/Loop3D/loopresources/commit/8724b6e4d9e12a160f594dd30f77978af560046a))
* change to add version in pyproject ([28b0251](https://github.com/Loop3D/loopresources/commit/28b0251f6f7d57a9190dd7b9a86874a939bfab0c))
* don't list holes that are in collar but not survey ([7850a35](https://github.com/Loop3D/loopresources/commit/7850a3504913e136ed6ceefee77eda68b7a9fd42))
* get version from pyproject ([58195dd](https://github.com/Loop3D/loopresources/commit/58195dd5f538800eba198bf6599ff52a5e2de83f))
* incorrect postive dips down ([fa4372d](https://github.com/Loop3D/loopresources/commit/fa4372d922e233aa1569de61896fb99c90b33f2b))
* making code robust to bad input. Also return dip not inclination where dip was passed ([e7dc61b](https://github.com/Loop3D/loopresources/commit/e7dc61b26545676a2ab5fd66945431eee48836c3))
* map resample correctly ([ab58470](https://github.com/Loop3D/loopresources/commit/ab58470a13f20dae4b0a6f57b831d500c4a365a9))
* migrate to pyproject from setup.py ([c78608a](https://github.com/Loop3D/loopresources/commit/c78608ac2b8d4294a0e92f9f0370e8f52c066c2b))
* move drillhole to own file and add a class to wrap interpolation of xyz along depth ([57dc65c](https://github.com/Loop3D/loopresources/commit/57dc65c177fe0964f0502e7aff329bf27e45ec8d))
* pandas indexing creating incompatible arrays ([5c055b9](https://github.com/Loop3D/loopresources/commit/5c055b967cd905fba13ecaf5a109ffc65916738e))
* remove -z conversion and enforce - angle dips down ([a7ddc20](https://github.com/Loop3D/loopresources/commit/a7ddc20923c522a94ddd5d8de617afd5f7315102))
* remove add_ninety and dip_is_incl ([b16ed91](https://github.com/Loop3D/loopresources/commit/b16ed91388bb49569bfa9d22fb474eb2ed49e179))
* remove divide by 0 ([9dff175](https://github.com/Loop3D/loopresources/commit/9dff175291c117171fe7e38086ad9760230c80b8))
* removing unused modules ([5702dd5](https://github.com/Loop3D/loopresources/commit/5702dd569f7bff2a7d8be47660c5e373fa1ea9a2))
* try and guess the table type ([04f0506](https://github.com/Loop3D/loopresources/commit/04f05064a027b86964dff36bae699461cf070132))
* updating desurvey ([9412301](https://github.com/Loop3D/loopresources/commit/9412301417e2a6250e0523780436bc126e91cb13))
* use pd.rename to change column names ([687d101](https://github.com/Loop3D/loopresources/commit/687d10144ca53cf56feafd1687a0395a2c8d9635))
* use slerp instead of interp1 for orientation interpolation ([57781d0](https://github.com/Loop3D/loopresources/commit/57781d0283071d9efb31a70404416be44c03e070))
* use two/from to build grid and add merge intervals back in WARNING its slow ([ba37b52](https://github.com/Loop3D/loopresources/commit/ba37b52b74f76d4a71598d76b4f4fc735caa4338))
* variables from different tables desurveyed onto same interval ([abbe11f](https://github.com/Loop3D/loopresources/commit/abbe11fce479cfb69fe677086c3dfe9477e1ab6e))


### Documentation

* updating docstrings to be numpy compliant ([0dd5060](https://github.com/Loop3D/loopresources/commit/0dd5060edfac4744866fe02f2fdb1517426516a7))
