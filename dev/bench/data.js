window.BENCHMARK_DATA = {
  "lastUpdate": 1773178042934,
  "repoUrl": "https://github.com/zincware/asebytes",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "name": "Fabian Zills",
            "username": "PythonFZ",
            "email": "46721498+PythonFZ@users.noreply.github.com"
          },
          "committer": {
            "name": "GitHub",
            "username": "web-flow",
            "email": "noreply@github.com"
          },
          "id": "fa2713e504d6550269573385f326bc2b43d07255",
          "message": "fix(ci): use --frozen flag to prevent uv.lock drift in CI (#13)\n\nPrevents uv sync from modifying uv.lock during CI runs, which caused\nthe benchmark action to fail when switching to gh-pages branch.\n\nCo-authored-by: Claude Opus 4.6 <noreply@anthropic.com>",
          "timestamp": "2026-03-10T11:20:05Z",
          "url": "https://github.com/zincware/asebytes/commit/fa2713e504d6550269573385f326bc2b43d07255"
        },
        "date": 1773143058382,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 3349.4049869289893,
            "unit": "iter/sec",
            "range": "stddev: 0.00004544978842115266",
            "extra": "mean: 298.56049175972663 usec\nrounds: 1881"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 339.6467070144813,
            "unit": "iter/sec",
            "range": "stddev: 0.000029105887459726325",
            "extra": "mean: 2.944235817241012 msec\nrounds: 290"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[periodic_100]",
            "value": 3284.728961749284,
            "unit": "iter/sec",
            "range": "stddev: 0.00001077787231432168",
            "extra": "mean: 304.43912165813816 usec\nrounds: 2581"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 323.9192434151048,
            "unit": "iter/sec",
            "range": "stddev: 0.00008685947746522806",
            "extra": "mean: 3.0871892310469895 msec\nrounds: 277"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[ethanol_100]",
            "value": 131.17539358824672,
            "unit": "iter/sec",
            "range": "stddev: 0.0002951891521904133",
            "extra": "mean: 7.623380976000362 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 12.75623238835777,
            "unit": "iter/sec",
            "range": "stddev: 0.008134677295197488",
            "extra": "mean: 78.3930528666654 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[periodic_100]",
            "value": 48.72786060985387,
            "unit": "iter/sec",
            "range": "stddev: 0.0010774732341398223",
            "extra": "mean: 20.52214046511571 msec\nrounds: 43"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[periodic_1000]",
            "value": 4.995655149661941,
            "unit": "iter/sec",
            "range": "stddev: 0.0019794438784406995",
            "extra": "mean: 200.17394516666562 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[ethanol_100]",
            "value": 1900.5185139303358,
            "unit": "iter/sec",
            "range": "stddev: 0.000038288481223177846",
            "extra": "mean: 526.1721959929591 usec\nrounds: 1148"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 228.52863027162905,
            "unit": "iter/sec",
            "range": "stddev: 0.0001458657193530286",
            "extra": "mean: 4.37581933962235 msec\nrounds: 159"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[periodic_100]",
            "value": 1824.4050878612868,
            "unit": "iter/sec",
            "range": "stddev: 0.00001424829497947954",
            "extra": "mean: 548.1238824938159 usec\nrounds: 834"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[periodic_1000]",
            "value": 211.04598568769336,
            "unit": "iter/sec",
            "range": "stddev: 0.00004969918517053607",
            "extra": "mean: 4.738303819148703 msec\nrounds: 94"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 916.3530658787636,
            "unit": "iter/sec",
            "range": "stddev: 0.00003845629466138629",
            "extra": "mean: 1.0912824294869585 msec\nrounds: 156"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 251.38291046027473,
            "unit": "iter/sec",
            "range": "stddev: 0.00013431724109527228",
            "extra": "mean: 3.97799515555385 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[periodic_100]",
            "value": 927.1322831109836,
            "unit": "iter/sec",
            "range": "stddev: 0.00005271885105305797",
            "extra": "mean: 1.0785947358498933 msec\nrounds: 159"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 250.49427279418842,
            "unit": "iter/sec",
            "range": "stddev: 0.00009901338131078288",
            "extra": "mean: 3.992107239999143 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[ethanol_100]",
            "value": 342.59896142666173,
            "unit": "iter/sec",
            "range": "stddev: 0.00008876404467270151",
            "extra": "mean: 2.918864656903125 msec\nrounds: 239"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[ethanol_1000]",
            "value": 43.311281296165575,
            "unit": "iter/sec",
            "range": "stddev: 0.004122874081204823",
            "extra": "mean: 23.088672744681226 msec\nrounds: 47"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[periodic_100]",
            "value": 334.9711355983358,
            "unit": "iter/sec",
            "range": "stddev: 0.0000707480788234344",
            "extra": "mean: 2.9853318502018658 msec\nrounds: 247"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[periodic_1000]",
            "value": 46.74500384854086,
            "unit": "iter/sec",
            "range": "stddev: 0.0008804633850511273",
            "extra": "mean: 21.39266055555614 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[ethanol_100]",
            "value": 144.88797802830595,
            "unit": "iter/sec",
            "range": "stddev: 0.0001332369818894337",
            "extra": "mean: 6.9018838802805 msec\nrounds: 142"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[ethanol_1000]",
            "value": 14.565575378316533,
            "unit": "iter/sec",
            "range": "stddev: 0.0005839094030369875",
            "extra": "mean: 68.65502899999947 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[periodic_100]",
            "value": 89.30632586310385,
            "unit": "iter/sec",
            "range": "stddev: 0.00009193543939722918",
            "extra": "mean: 11.197415080460068 msec\nrounds: 87"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[periodic_1000]",
            "value": 8.796440600456517,
            "unit": "iter/sec",
            "range": "stddev: 0.0009801056364525367",
            "extra": "mean: 113.6823455555537 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[ethanol_100]",
            "value": 1665.8690488217417,
            "unit": "iter/sec",
            "range": "stddev: 0.000032472100766483465",
            "extra": "mean: 600.2872799079216 usec\nrounds: 1304"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[ethanol_1000]",
            "value": 252.27087300091478,
            "unit": "iter/sec",
            "range": "stddev: 0.012243363001513838",
            "extra": "mean: 3.9639931003702276 msec\nrounds: 269"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[periodic_100]",
            "value": 848.4483623488169,
            "unit": "iter/sec",
            "range": "stddev: 0.00013840963002086584",
            "extra": "mean: 1.1786221111107251 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[periodic_1000]",
            "value": 120.42132579160885,
            "unit": "iter/sec",
            "range": "stddev: 0.012283734081260973",
            "extra": "mean: 8.304176967213573 msec\nrounds: 122"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[ethanol_100]",
            "value": 54.0234430653973,
            "unit": "iter/sec",
            "range": "stddev: 0.00013829654345970738",
            "extra": "mean: 18.51048254716872 msec\nrounds: 53"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[ethanol_1000]",
            "value": 5.476738123488408,
            "unit": "iter/sec",
            "range": "stddev: 0.0008599831411090059",
            "extra": "mean: 182.59043566666833 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[periodic_100]",
            "value": 52.98957560841059,
            "unit": "iter/sec",
            "range": "stddev: 0.00033014465389316985",
            "extra": "mean: 18.87163632692462 msec\nrounds: 52"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[periodic_1000]",
            "value": 5.47477517685182,
            "unit": "iter/sec",
            "range": "stddev: 0.003915501601785254",
            "extra": "mean: 182.65590233333265 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[ethanol_100]",
            "value": 373.2680433960228,
            "unit": "iter/sec",
            "range": "stddev: 0.0002610289643905401",
            "extra": "mean: 2.6790399491526764 msec\nrounds: 354"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[ethanol_1000]",
            "value": 37.442614992877544,
            "unit": "iter/sec",
            "range": "stddev: 0.0002511025386662212",
            "extra": "mean: 26.707536324325194 msec\nrounds: 37"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[periodic_100]",
            "value": 413.96918309891134,
            "unit": "iter/sec",
            "range": "stddev: 0.00003461648907540303",
            "extra": "mean: 2.4156387500010257 msec\nrounds: 388"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[periodic_1000]",
            "value": 39.754362280577865,
            "unit": "iter/sec",
            "range": "stddev: 0.0019284297943696624",
            "extra": "mean: 25.15447217948591 msec\nrounds: 39"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[ethanol_100]",
            "value": 1.4133922707809325,
            "unit": "iter/sec",
            "range": "stddev: 0.01284154726049327",
            "extra": "mean: 707.517665599994 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[ethanol_1000]",
            "value": 0.1390783146351421,
            "unit": "iter/sec",
            "range": "stddev: 0.0870405222103356",
            "extra": "mean: 7.190193544000005 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[periodic_100]",
            "value": 1.4501508705207347,
            "unit": "iter/sec",
            "range": "stddev: 0.05172343721797523",
            "extra": "mean: 689.5834222000019 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[periodic_1000]",
            "value": 0.14783608266956916,
            "unit": "iter/sec",
            "range": "stddev: 0.0746426278760348",
            "extra": "mean: 6.764248496999994 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[ethanol_100]",
            "value": 11.285952039288736,
            "unit": "iter/sec",
            "range": "stddev: 0.004828319311763587",
            "extra": "mean: 88.60572829999569 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[ethanol_1000]",
            "value": 1.1448289423223197,
            "unit": "iter/sec",
            "range": "stddev: 0.006807785535982689",
            "extra": "mean: 873.4929411999929 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[periodic_100]",
            "value": 15.089219901573683,
            "unit": "iter/sec",
            "range": "stddev: 0.0006531075440952101",
            "extra": "mean: 66.27247840000715 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[periodic_1000]",
            "value": 1.4777820422002688,
            "unit": "iter/sec",
            "range": "stddev: 0.019765229171742085",
            "extra": "mean: 676.6897766000056 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[ethanol_100]",
            "value": 26.011843556534693,
            "unit": "iter/sec",
            "range": "stddev: 0.000996792211238469",
            "extra": "mean: 38.44402638461894 msec\nrounds: 26"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.5600740276740983,
            "unit": "iter/sec",
            "range": "stddev: 0.003475434887815307",
            "extra": "mean: 390.61370459999125 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[periodic_100]",
            "value": 25.315217232575392,
            "unit": "iter/sec",
            "range": "stddev: 0.0028907729530775784",
            "extra": "mean: 39.50193240740629 msec\nrounds: 27"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[periodic_1000]",
            "value": 2.4907195019234947,
            "unit": "iter/sec",
            "range": "stddev: 0.028835820420090082",
            "extra": "mean: 401.4904124000054 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[ethanol_100]",
            "value": 37.468279182287425,
            "unit": "iter/sec",
            "range": "stddev: 0.0014104462950728753",
            "extra": "mean: 26.689242789477643 msec\nrounds: 38"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[ethanol_1000]",
            "value": 3.643113828174234,
            "unit": "iter/sec",
            "range": "stddev: 0.003472653380368775",
            "extra": "mean: 274.4904625999993 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[periodic_100]",
            "value": 39.11110243935928,
            "unit": "iter/sec",
            "range": "stddev: 0.0009455010841669419",
            "extra": "mean: 25.568187487184062 msec\nrounds: 39"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[periodic_1000]",
            "value": 3.7990439680019565,
            "unit": "iter/sec",
            "range": "stddev: 0.007509058435362542",
            "extra": "mean: 263.2241186000101 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[ethanol_100]",
            "value": 139.9377079814283,
            "unit": "iter/sec",
            "range": "stddev: 0.00007377023802672385",
            "extra": "mean: 7.146036721801345 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[ethanol_1000]",
            "value": 13.76017494293211,
            "unit": "iter/sec",
            "range": "stddev: 0.0004665473805984842",
            "extra": "mean: 72.6734946428605 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[periodic_100]",
            "value": 80.91307200325431,
            "unit": "iter/sec",
            "range": "stddev: 0.0014278096666177885",
            "extra": "mean: 12.35894244578651 msec\nrounds: 83"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[periodic_1000]",
            "value": 8.459480034336933,
            "unit": "iter/sec",
            "range": "stddev: 0.00283846930495629",
            "extra": "mean: 118.2105751111193 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[ethanol_100]",
            "value": 2.1778055100692697,
            "unit": "iter/sec",
            "range": "stddev: 0.0017761686007924447",
            "extra": "mean: 459.1778262000048 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[ethanol_1000]",
            "value": 0.21616665868466978,
            "unit": "iter/sec",
            "range": "stddev: 0.04706640398257613",
            "extra": "mean: 4.626060309599995 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[periodic_100]",
            "value": 2.419097717105275,
            "unit": "iter/sec",
            "range": "stddev: 0.008816922372712428",
            "extra": "mean: 413.3772657999998 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[periodic_1000]",
            "value": 0.24287498441047387,
            "unit": "iter/sec",
            "range": "stddev: 0.03088772849518172",
            "extra": "mean: 4.1173445772000035 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[ethanol_100]",
            "value": 25.08423446472919,
            "unit": "iter/sec",
            "range": "stddev: 0.00038138577929418884",
            "extra": "mean: 39.86567743999103 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[ethanol_1000]",
            "value": 2.4968813577310116,
            "unit": "iter/sec",
            "range": "stddev: 0.0015499256533154124",
            "extra": "mean: 400.49960599999395 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[periodic_100]",
            "value": 25.175876964514984,
            "unit": "iter/sec",
            "range": "stddev: 0.00026692411145136727",
            "extra": "mean: 39.72056271999918 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[periodic_1000]",
            "value": 2.385981828406381,
            "unit": "iter/sec",
            "range": "stddev: 0.027181374568180882",
            "extra": "mean: 419.1146755999853 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[ethanol_100]",
            "value": 9280.236661773553,
            "unit": "iter/sec",
            "range": "stddev: 0.0000057483584070655336",
            "extra": "mean: 107.75587266207596 usec\nrounds: 4170"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[ethanol_1000]",
            "value": 843.9619639245857,
            "unit": "iter/sec",
            "range": "stddev: 0.000017188500134337335",
            "extra": "mean: 1.1848875218852368 msec\nrounds: 594"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[periodic_100]",
            "value": 9275.076317933625,
            "unit": "iter/sec",
            "range": "stddev: 0.000005431041355653964",
            "extra": "mean: 107.8158244441042 usec\nrounds: 5531"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[periodic_1000]",
            "value": 849.583645137877,
            "unit": "iter/sec",
            "range": "stddev: 0.000022437248775418694",
            "extra": "mean: 1.1770471403527458 msec\nrounds: 570"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[ethanol_100]",
            "value": 730.7890027308256,
            "unit": "iter/sec",
            "range": "stddev: 0.00008371257383578488",
            "extra": "mean: 1.3683840291290397 msec\nrounds: 618"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[ethanol_1000]",
            "value": 98.99115992199638,
            "unit": "iter/sec",
            "range": "stddev: 0.00036250338906689244",
            "extra": "mean: 10.101912138295841 msec\nrounds: 94"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[periodic_100]",
            "value": 730.4044641257943,
            "unit": "iter/sec",
            "range": "stddev: 0.00008722973757029502",
            "extra": "mean: 1.3691044470776597 msec\nrounds: 633"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[periodic_1000]",
            "value": 98.84166780263264,
            "unit": "iter/sec",
            "range": "stddev: 0.000447175234465885",
            "extra": "mean: 10.117190677081686 msec\nrounds: 96"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[ethanol_100]",
            "value": 3222.0638323908815,
            "unit": "iter/sec",
            "range": "stddev: 0.0000395276142799753",
            "extra": "mean: 310.36008348039644 usec\nrounds: 2264"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[ethanol_1000]",
            "value": 432.7070612996251,
            "unit": "iter/sec",
            "range": "stddev: 0.0003673403223875317",
            "extra": "mean: 2.311032311320561 msec\nrounds: 424"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[periodic_100]",
            "value": 3267.3728075254558,
            "unit": "iter/sec",
            "range": "stddev: 0.000020984003820948672",
            "extra": "mean: 306.0562901474808 usec\nrounds: 2578"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[periodic_1000]",
            "value": 466.700439724611,
            "unit": "iter/sec",
            "range": "stddev: 0.00005196297036024231",
            "extra": "mean: 2.1427020737115154 msec\nrounds: 407"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[ethanol_100]",
            "value": 935.0422086842241,
            "unit": "iter/sec",
            "range": "stddev: 0.00003422696456563442",
            "extra": "mean: 1.069470437497344 msec\nrounds: 160"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[ethanol_1000]",
            "value": 245.56077683241836,
            "unit": "iter/sec",
            "range": "stddev: 0.00009114601181309709",
            "extra": "mean: 4.07231160000135 msec\nrounds: 105"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[periodic_100]",
            "value": 928.1110395990236,
            "unit": "iter/sec",
            "range": "stddev: 0.00004341478516855524",
            "extra": "mean: 1.077457284025018 msec\nrounds: 169"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[periodic_1000]",
            "value": 187.43762109443833,
            "unit": "iter/sec",
            "range": "stddev: 0.012876434041829364",
            "extra": "mean: 5.335108257142045 msec\nrounds: 105"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[ethanol_100]",
            "value": 372.698451094562,
            "unit": "iter/sec",
            "range": "stddev: 0.00007643582257186416",
            "extra": "mean: 2.68313430620155 msec\nrounds: 258"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[ethanol_1000]",
            "value": 53.115121175068644,
            "unit": "iter/sec",
            "range": "stddev: 0.0005864895130953463",
            "extra": "mean: 18.827030379992493 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[periodic_100]",
            "value": 363.61944371908515,
            "unit": "iter/sec",
            "range": "stddev: 0.0003232611571283643",
            "extra": "mean: 2.7501279628285 msec\nrounds: 269"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[periodic_1000]",
            "value": 53.951139129280605,
            "unit": "iter/sec",
            "range": "stddev: 0.00043906220098184807",
            "extra": "mean: 18.53528982221759 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[ethanol_100]",
            "value": 148.12548205384746,
            "unit": "iter/sec",
            "range": "stddev: 0.00022511386749852227",
            "extra": "mean: 6.751032881948523 msec\nrounds: 144"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[ethanol_1000]",
            "value": 13.791261506411798,
            "unit": "iter/sec",
            "range": "stddev: 0.0072954794300409236",
            "extra": "mean: 72.5096829999984 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[periodic_100]",
            "value": 88.33064902414432,
            "unit": "iter/sec",
            "range": "stddev: 0.00010673652129955241",
            "extra": "mean: 11.321098747125243 msec\nrounds: 87"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[periodic_1000]",
            "value": 8.828670571682721,
            "unit": "iter/sec",
            "range": "stddev: 0.0004843693178821988",
            "extra": "mean: 113.26733644444984 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[ethanol_100]",
            "value": 2577.6592764319917,
            "unit": "iter/sec",
            "range": "stddev: 0.00001580739008304918",
            "extra": "mean: 387.948868627899 usec\nrounds: 1903"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[ethanol_1000]",
            "value": 2052.2770123466826,
            "unit": "iter/sec",
            "range": "stddev: 0.000019702176604974773",
            "extra": "mean: 487.26365592164717 usec\nrounds: 1520"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[periodic_100]",
            "value": 2586.622787283513,
            "unit": "iter/sec",
            "range": "stddev: 0.000018065418400454827",
            "extra": "mean: 386.6044963789274 usec\nrounds: 2071"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[periodic_1000]",
            "value": 2050.225316613652,
            "unit": "iter/sec",
            "range": "stddev: 0.000020369058058704943",
            "extra": "mean: 487.75126904183173 usec\nrounds: 1628"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[ethanol_100]",
            "value": 62.28955753798885,
            "unit": "iter/sec",
            "range": "stddev: 0.0006337934957380631",
            "extra": "mean: 16.05405527868977 msec\nrounds: 61"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[ethanol_1000]",
            "value": 6.421889339347582,
            "unit": "iter/sec",
            "range": "stddev: 0.001611443119306977",
            "extra": "mean: 155.7174138571489 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[periodic_100]",
            "value": 63.467195205634646,
            "unit": "iter/sec",
            "range": "stddev: 0.000203120999253416",
            "extra": "mean: 15.756171306451867 msec\nrounds: 62"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[periodic_1000]",
            "value": 6.443045558824278,
            "unit": "iter/sec",
            "range": "stddev: 0.0007857322463185658",
            "extra": "mean: 155.20610414284874 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 238.66961678765165,
            "unit": "iter/sec",
            "range": "stddev: 0.0012596265920058914",
            "extra": "mean: 4.189892343480472 msec\nrounds: 230"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 23.885062404580225,
            "unit": "iter/sec",
            "range": "stddev: 0.0021165933684860953",
            "extra": "mean: 41.86717133333673 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[periodic_100]",
            "value": 280.3034431530381,
            "unit": "iter/sec",
            "range": "stddev: 0.0003829965055632307",
            "extra": "mean: 3.5675623130110004 msec\nrounds: 246"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 21.008579131655726,
            "unit": "iter/sec",
            "range": "stddev: 0.028103855234580935",
            "extra": "mean: 47.59960174999175 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[ethanol_100]",
            "value": 24.32894721882313,
            "unit": "iter/sec",
            "range": "stddev: 0.0015415060920849887",
            "extra": "mean: 41.10329933332698 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 2.862687968801085,
            "unit": "iter/sec",
            "range": "stddev: 0.0033534376564489463",
            "extra": "mean: 349.32203960000834 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[periodic_100]",
            "value": 11.207794870538269,
            "unit": "iter/sec",
            "range": "stddev: 0.002088370619300314",
            "extra": "mean: 89.22361727271456 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[periodic_1000]",
            "value": 1.1407734623723964,
            "unit": "iter/sec",
            "range": "stddev: 0.06031512451985392",
            "extra": "mean: 876.5982317999942 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[ethanol_100]",
            "value": 207.98466747603118,
            "unit": "iter/sec",
            "range": "stddev: 0.00039786936817975065",
            "extra": "mean: 4.808046728325507 msec\nrounds: 173"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 20.015207119256033,
            "unit": "iter/sec",
            "range": "stddev: 0.03375107905700983",
            "extra": "mean: 49.96201108695647 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[periodic_100]",
            "value": 234.37417591814705,
            "unit": "iter/sec",
            "range": "stddev: 0.0005842609418174064",
            "extra": "mean: 4.266681668671725 msec\nrounds: 166"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[periodic_1000]",
            "value": 26.255783883351256,
            "unit": "iter/sec",
            "range": "stddev: 0.0031767845302533644",
            "extra": "mean: 38.08684609999773 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 248.04436233574268,
            "unit": "iter/sec",
            "range": "stddev: 0.0008384757111725256",
            "extra": "mean: 4.031536901638752 msec\nrounds: 244"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 21.232495157229295,
            "unit": "iter/sec",
            "range": "stddev: 0.03299761849452965",
            "extra": "mean: 47.09762053846589 msec\nrounds: 26"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[periodic_100]",
            "value": 202.6553064553071,
            "unit": "iter/sec",
            "range": "stddev: 0.011671453421618396",
            "extra": "mean: 4.934487122450635 msec\nrounds: 245"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 26.546522239341787,
            "unit": "iter/sec",
            "range": "stddev: 0.004465204864292602",
            "extra": "mean: 37.66971774999612 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[ethanol_100]",
            "value": 127.50683227255685,
            "unit": "iter/sec",
            "range": "stddev: 0.0018030423679244473",
            "extra": "mean: 7.842716991528845 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[ethanol_1000]",
            "value": 10.443314508648276,
            "unit": "iter/sec",
            "range": "stddev: 0.05672647115343217",
            "extra": "mean: 95.75504014284775 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[periodic_100]",
            "value": 146.62019716972196,
            "unit": "iter/sec",
            "range": "stddev: 0.0005971557204687503",
            "extra": "mean: 6.820342758388451 msec\nrounds: 149"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[periodic_1000]",
            "value": 13.51937659538715,
            "unit": "iter/sec",
            "range": "stddev: 0.039534973791270266",
            "extra": "mean: 73.96790768748929 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[ethanol_100]",
            "value": 57.44934247975116,
            "unit": "iter/sec",
            "range": "stddev: 0.0016064332413294354",
            "extra": "mean: 17.406639603446536 msec\nrounds: 58"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[ethanol_1000]",
            "value": 5.697414573658383,
            "unit": "iter/sec",
            "range": "stddev: 0.007327382900001521",
            "extra": "mean: 175.51820866668777 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[periodic_100]",
            "value": 44.5811983963203,
            "unit": "iter/sec",
            "range": "stddev: 0.0009525311528287056",
            "extra": "mean: 22.430980681814493 msec\nrounds: 44"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[periodic_1000]",
            "value": 4.380270215190325,
            "unit": "iter/sec",
            "range": "stddev: 0.0017211905755563411",
            "extra": "mean: 228.2964179999908 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[ethanol_100]",
            "value": 2.1641642494604287,
            "unit": "iter/sec",
            "range": "stddev: 0.004009535133869772",
            "extra": "mean: 462.07213719999345 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[ethanol_1000]",
            "value": 0.21450998180870692,
            "unit": "iter/sec",
            "range": "stddev: 0.08377321477980972",
            "extra": "mean: 4.6617877246000035 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[periodic_100]",
            "value": 2.391871352265595,
            "unit": "iter/sec",
            "range": "stddev: 0.016754043032262023",
            "extra": "mean: 418.082686199989 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[periodic_1000]",
            "value": 0.24078634025856824,
            "unit": "iter/sec",
            "range": "stddev: 0.040262792912584236",
            "extra": "mean: 4.153059508800004 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[ethanol_100]",
            "value": 17.20351096386705,
            "unit": "iter/sec",
            "range": "stddev: 0.008002316883980717",
            "extra": "mean: 58.12766952631495 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[ethanol_1000]",
            "value": 1.8381748249237646,
            "unit": "iter/sec",
            "range": "stddev: 0.0044854581028509095",
            "extra": "mean: 544.0178956000409 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[periodic_100]",
            "value": 18.314594346454193,
            "unit": "iter/sec",
            "range": "stddev: 0.0016449284166785464",
            "extra": "mean: 54.60126394738334 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[periodic_1000]",
            "value": 1.710221158507771,
            "unit": "iter/sec",
            "range": "stddev: 0.08791411836004473",
            "extra": "mean: 584.719698400022 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[ethanol_100]",
            "value": 212.6662169469271,
            "unit": "iter/sec",
            "range": "stddev: 0.0007561441671232185",
            "extra": "mean: 4.702204300975362 msec\nrounds: 103"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[ethanol_1000]",
            "value": 17.193976941686422,
            "unit": "iter/sec",
            "range": "stddev: 0.04038138519457736",
            "extra": "mean: 58.15990119048733 msec\nrounds: 21"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[periodic_100]",
            "value": 236.3135677005597,
            "unit": "iter/sec",
            "range": "stddev: 0.0004885352909635231",
            "extra": "mean: 4.231665620093092 msec\nrounds: 229"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[periodic_1000]",
            "value": 21.91789502397283,
            "unit": "iter/sec",
            "range": "stddev: 0.0036178169389449143",
            "extra": "mean: 45.62481930432845 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[ethanol_100]",
            "value": 1.3578452410790054,
            "unit": "iter/sec",
            "range": "stddev: 0.044709246506599506",
            "extra": "mean: 736.4609528000074 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[ethanol_1000]",
            "value": 0.14278422084642992,
            "unit": "iter/sec",
            "range": "stddev: 0.10160544243123719",
            "extra": "mean: 7.0035750033999875 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[periodic_100]",
            "value": 1.5345779127276273,
            "unit": "iter/sec",
            "range": "stddev: 0.013617214631710834",
            "extra": "mean: 651.6449844000135 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[periodic_1000]",
            "value": 0.15110239473280324,
            "unit": "iter/sec",
            "range": "stddev: 0.05670476084988558",
            "extra": "mean: 6.618028799400008 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[ethanol_100]",
            "value": 11.186509698729523,
            "unit": "iter/sec",
            "range": "stddev: 0.0030209099560554033",
            "extra": "mean: 89.39338783334468 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[ethanol_1000]",
            "value": 1.1306924162440672,
            "unit": "iter/sec",
            "range": "stddev: 0.005781908265725513",
            "extra": "mean: 884.4138208000004 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[periodic_100]",
            "value": 14.706867698658678,
            "unit": "iter/sec",
            "range": "stddev: 0.0009899749991343042",
            "extra": "mean: 67.99544406666578 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[periodic_1000]",
            "value": 1.4667058657303114,
            "unit": "iter/sec",
            "range": "stddev: 0.006802973313672638",
            "extra": "mean: 681.7999595999936 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[ethanol_100]",
            "value": 23.55239268860553,
            "unit": "iter/sec",
            "range": "stddev: 0.0011376069271853912",
            "extra": "mean: 42.45853120832995 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.145035844426205,
            "unit": "iter/sec",
            "range": "stddev: 0.07613331069542065",
            "extra": "mean: 466.19267580001633 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[periodic_100]",
            "value": 23.51027168373595,
            "unit": "iter/sec",
            "range": "stddev: 0.0017748160915098193",
            "extra": "mean: 42.53459991667322 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[periodic_1000]",
            "value": 2.290971316589278,
            "unit": "iter/sec",
            "range": "stddev: 0.026609262629622304",
            "extra": "mean: 436.4960803999793 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[ethanol_100]",
            "value": 31.931189927890895,
            "unit": "iter/sec",
            "range": "stddev: 0.0021726708190273796",
            "extra": "mean: 31.317342142847338 msec\nrounds: 35"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[ethanol_1000]",
            "value": 3.2120701868095067,
            "unit": "iter/sec",
            "range": "stddev: 0.0035072232623946597",
            "extra": "mean: 311.3257001999955 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[periodic_100]",
            "value": 32.901124666666554,
            "unit": "iter/sec",
            "range": "stddev: 0.0019020191873047642",
            "extra": "mean: 30.394097774205875 msec\nrounds: 31"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[periodic_1000]",
            "value": 3.308715031050404,
            "unit": "iter/sec",
            "range": "stddev: 0.005318506121923724",
            "extra": "mean: 302.2321325999883 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[ethanol_100]",
            "value": 58.54798982283267,
            "unit": "iter/sec",
            "range": "stddev: 0.0012470355744718345",
            "extra": "mean: 17.08000570175029 msec\nrounds: 57"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[ethanol_1000]",
            "value": 5.800140756655254,
            "unit": "iter/sec",
            "range": "stddev: 0.003738231848715244",
            "extra": "mean: 172.40960900001787 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[periodic_100]",
            "value": 44.610776816272434,
            "unit": "iter/sec",
            "range": "stddev: 0.001323821748690634",
            "extra": "mean: 22.416108200008644 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[periodic_1000]",
            "value": 4.391966411098275,
            "unit": "iter/sec",
            "range": "stddev: 0.00401332363609122",
            "extra": "mean: 227.68844439999611 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[ethanol_100]",
            "value": 2.1584447043495345,
            "unit": "iter/sec",
            "range": "stddev: 0.0023532410473943314",
            "extra": "mean: 463.29655699998966 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[ethanol_1000]",
            "value": 0.2149788930792615,
            "unit": "iter/sec",
            "range": "stddev: 0.06494915333068596",
            "extra": "mean: 4.651619448199995 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[periodic_100]",
            "value": 2.4394511871036606,
            "unit": "iter/sec",
            "range": "stddev: 0.005666690421097968",
            "extra": "mean: 409.9282680000215 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[periodic_1000]",
            "value": 0.24147401748533007,
            "unit": "iter/sec",
            "range": "stddev: 0.035078801676903235",
            "extra": "mean: 4.141232296599992 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[ethanol_100]",
            "value": 18.52975381621878,
            "unit": "iter/sec",
            "range": "stddev: 0.0018753564740832207",
            "extra": "mean: 53.96725773683604 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[ethanol_1000]",
            "value": 1.8448212939286412,
            "unit": "iter/sec",
            "range": "stddev: 0.004017775667560846",
            "extra": "mean: 542.0579235999867 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[periodic_100]",
            "value": 17.94591861261173,
            "unit": "iter/sec",
            "range": "stddev: 0.0036885011356197974",
            "extra": "mean: 55.72297643750801 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[periodic_1000]",
            "value": 1.8161650929870843,
            "unit": "iter/sec",
            "range": "stddev: 0.009776718234633552",
            "extra": "mean: 550.6107367999675 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 226.72790577659953,
            "unit": "iter/sec",
            "range": "stddev: 0.0016442326349110957",
            "extra": "mean: 4.410573090130882 msec\nrounds: 233"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 16.79891673220403,
            "unit": "iter/sec",
            "range": "stddev: 0.04860950735132512",
            "extra": "mean: 59.52764787999513 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[periodic_100]",
            "value": 228.7397968185906,
            "unit": "iter/sec",
            "range": "stddev: 0.010451659045265679",
            "extra": "mean: 4.371779698628839 msec\nrounds: 219"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 19.188044256375527,
            "unit": "iter/sec",
            "range": "stddev: 0.03790779488554345",
            "extra": "mean: 52.115785571410406 msec\nrounds: 21"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[ethanol_100]",
            "value": 23.68996614182764,
            "unit": "iter/sec",
            "range": "stddev: 0.0016245420630937627",
            "extra": "mean: 42.21196408695466 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 2.7883779716851045,
            "unit": "iter/sec",
            "range": "stddev: 0.004425007511284575",
            "extra": "mean: 358.6314374000267 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[periodic_100]",
            "value": 11.222363691440217,
            "unit": "iter/sec",
            "range": "stddev: 0.0017294785358393113",
            "extra": "mean: 89.10778758335407 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[periodic_1000]",
            "value": 1.1584880753871678,
            "unit": "iter/sec",
            "range": "stddev: 0.037494374778308796",
            "extra": "mean: 863.1940382000039 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[ethanol_100]",
            "value": 190.63117246404408,
            "unit": "iter/sec",
            "range": "stddev: 0.00047070726920692417",
            "extra": "mean: 5.245731781818711 msec\nrounds: 165"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 19.262213842340593,
            "unit": "iter/sec",
            "range": "stddev: 0.03559559595163736",
            "extra": "mean: 51.91511257142641 msec\nrounds: 21"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[periodic_100]",
            "value": 224.8093472217189,
            "unit": "iter/sec",
            "range": "stddev: 0.0006153607530704064",
            "extra": "mean: 4.448213619043815 msec\nrounds: 168"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[periodic_1000]",
            "value": 26.03462077621444,
            "unit": "iter/sec",
            "range": "stddev: 0.0030558548946491614",
            "extra": "mean: 38.41039240001578 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 222.40884541505628,
            "unit": "iter/sec",
            "range": "stddev: 0.0016074978356725598",
            "extra": "mean: 4.496224051403235 msec\nrounds: 214"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 18.716991527289224,
            "unit": "iter/sec",
            "range": "stddev: 0.03723757522110552",
            "extra": "mean: 53.427389681830434 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[periodic_100]",
            "value": 241.9192263365694,
            "unit": "iter/sec",
            "range": "stddev: 0.0017439364856676029",
            "extra": "mean: 4.133611102942074 msec\nrounds: 136"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 25.54369639173763,
            "unit": "iter/sec",
            "range": "stddev: 0.004439044163243415",
            "extra": "mean: 39.148601857147824 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[ethanol_100]",
            "value": 132.95717786506398,
            "unit": "iter/sec",
            "range": "stddev: 0.0015227119086855798",
            "extra": "mean: 7.521218606301071 msec\nrounds: 127"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[ethanol_1000]",
            "value": 14.927162477797737,
            "unit": "iter/sec",
            "range": "stddev: 0.003254967207755819",
            "extra": "mean: 66.99196860001848 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[periodic_100]",
            "value": 148.96967583669255,
            "unit": "iter/sec",
            "range": "stddev: 0.0006067279331003554",
            "extra": "mean: 6.712775565788613 msec\nrounds: 152"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[periodic_1000]",
            "value": 13.71459362558268,
            "unit": "iter/sec",
            "range": "stddev: 0.03929885884008938",
            "extra": "mean: 72.91502958823645 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[ethanol_100]",
            "value": 61.13801154105632,
            "unit": "iter/sec",
            "range": "stddev: 0.0012077799880944042",
            "extra": "mean: 16.3564364426289 msec\nrounds: 61"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[ethanol_1000]",
            "value": 6.086241370737874,
            "unit": "iter/sec",
            "range": "stddev: 0.0024472699562969147",
            "extra": "mean: 164.30501833330405 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[periodic_100]",
            "value": 42.56602386580644,
            "unit": "iter/sec",
            "range": "stddev: 0.004248341664085149",
            "extra": "mean: 23.492915456529317 msec\nrounds: 46"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[periodic_1000]",
            "value": 3.9676538322716763,
            "unit": "iter/sec",
            "range": "stddev: 0.0714767907983327",
            "extra": "mean: 252.03811679998577 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[ethanol_100]",
            "value": 52.27358297048743,
            "unit": "iter/sec",
            "range": "stddev: 0.001087287256065051",
            "extra": "mean: 19.130121625000893 msec\nrounds: 56"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[ethanol_1000]",
            "value": 7.1851379330572005,
            "unit": "iter/sec",
            "range": "stddev: 0.0031058226675191574",
            "extra": "mean: 139.17617299999563 msec\nrounds: 8"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[periodic_100]",
            "value": 56.93895205521734,
            "unit": "iter/sec",
            "range": "stddev: 0.0016189221433981534",
            "extra": "mean: 17.56266955932445 msec\nrounds: 59"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[periodic_1000]",
            "value": 7.467118483090053,
            "unit": "iter/sec",
            "range": "stddev: 0.005067823258195124",
            "extra": "mean: 133.9204677499879 msec\nrounds: 8"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[ethanol_100]",
            "value": 30.896209837052098,
            "unit": "iter/sec",
            "range": "stddev: 0.0013091760661330123",
            "extra": "mean: 32.36642958065219 msec\nrounds: 31"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[ethanol_1000]",
            "value": 2.8045728066007727,
            "unit": "iter/sec",
            "range": "stddev: 0.08627185565094371",
            "extra": "mean: 356.56054199998835 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[periodic_100]",
            "value": 29.6345631038856,
            "unit": "iter/sec",
            "range": "stddev: 0.0017333837939729503",
            "extra": "mean: 33.74438140000393 msec\nrounds: 30"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[periodic_1000]",
            "value": 2.9936028168683464,
            "unit": "iter/sec",
            "range": "stddev: 0.0035741040128502797",
            "extra": "mean: 334.04565039998033 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[ethanol_100]",
            "value": 32.864273048919706,
            "unit": "iter/sec",
            "range": "stddev: 0.0009007953013422592",
            "extra": "mean: 30.428179516140897 msec\nrounds: 31"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[ethanol_1000]",
            "value": 3.1501522310125156,
            "unit": "iter/sec",
            "range": "stddev: 0.020968972031497248",
            "extra": "mean: 317.444976199954 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[periodic_100]",
            "value": 31.883897084417374,
            "unit": "iter/sec",
            "range": "stddev: 0.002428040941879185",
            "extra": "mean: 31.363794624990504 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[periodic_1000]",
            "value": 2.714707133243729,
            "unit": "iter/sec",
            "range": "stddev: 0.09647525880303282",
            "extra": "mean: 368.36386059999313 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[ethanol_100]",
            "value": 206.40324452581018,
            "unit": "iter/sec",
            "range": "stddev: 0.0010410006365927824",
            "extra": "mean: 4.844885080645874 msec\nrounds: 186"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[ethanol_1000]",
            "value": 17.30553641819192,
            "unit": "iter/sec",
            "range": "stddev: 0.04006653316095809",
            "extra": "mean: 57.784975619061434 msec\nrounds: 21"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[periodic_100]",
            "value": 215.8623485007575,
            "unit": "iter/sec",
            "range": "stddev: 0.001054677467272094",
            "extra": "mean: 4.63258186036316 msec\nrounds: 222"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[periodic_1000]",
            "value": 18.92830624187365,
            "unit": "iter/sec",
            "range": "stddev: 0.03860972797734743",
            "extra": "mean: 52.83092883333514 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[ethanol_100]",
            "value": 1.4161884383122867,
            "unit": "iter/sec",
            "range": "stddev: 0.02057962440565097",
            "extra": "mean: 706.1207202000105 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[ethanol_1000]",
            "value": 0.1423591556277873,
            "unit": "iter/sec",
            "range": "stddev: 0.08472851658097025",
            "extra": "mean: 7.024486732799983 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[periodic_100]",
            "value": 1.5247730177142509,
            "unit": "iter/sec",
            "range": "stddev: 0.013929784859491366",
            "extra": "mean: 655.8353200000056 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[periodic_1000]",
            "value": 0.1506806230392381,
            "unit": "iter/sec",
            "range": "stddev: 0.08031857102305305",
            "extra": "mean: 6.636553392399992 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[ethanol_100]",
            "value": 11.369030581066703,
            "unit": "iter/sec",
            "range": "stddev: 0.0004084221555954007",
            "extra": "mean: 87.95824699999837 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[ethanol_1000]",
            "value": 1.0766076930141417,
            "unit": "iter/sec",
            "range": "stddev: 0.08681498127161924",
            "extra": "mean: 928.843446399992 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[periodic_100]",
            "value": 14.755340837757076,
            "unit": "iter/sec",
            "range": "stddev: 0.002050057575172987",
            "extra": "mean: 67.77207053334375 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[periodic_1000]",
            "value": 1.463606982803899,
            "unit": "iter/sec",
            "range": "stddev: 0.007379669295728747",
            "extra": "mean: 683.2435290000149 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[ethanol_100]",
            "value": 23.412496688180486,
            "unit": "iter/sec",
            "range": "stddev: 0.001722217043273064",
            "extra": "mean: 42.71223241666652 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.2422008898631516,
            "unit": "iter/sec",
            "range": "stddev: 0.03212428112753849",
            "extra": "mean: 445.9903680000025 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[periodic_100]",
            "value": 23.566155097149448,
            "unit": "iter/sec",
            "range": "stddev: 0.0006488795933752593",
            "extra": "mean: 42.43373583334176 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[periodic_1000]",
            "value": 2.3506374908894703,
            "unit": "iter/sec",
            "range": "stddev: 0.008343519185901772",
            "extra": "mean: 425.4165110000031 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[ethanol_100]",
            "value": 32.847433198545325,
            "unit": "iter/sec",
            "range": "stddev: 0.0018427703671361898",
            "extra": "mean: 30.443779090911917 msec\nrounds: 33"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[ethanol_1000]",
            "value": 3.109448623260505,
            "unit": "iter/sec",
            "range": "stddev: 0.04059830076770709",
            "extra": "mean: 321.6004253999927 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[periodic_100]",
            "value": 30.42189474644978,
            "unit": "iter/sec",
            "range": "stddev: 0.003567317960004241",
            "extra": "mean: 32.871062382355376 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[periodic_1000]",
            "value": 3.2322388007606855,
            "unit": "iter/sec",
            "range": "stddev: 0.0028106574685079332",
            "extra": "mean: 309.3830814000057 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[ethanol_100]",
            "value": 58.44256373613412,
            "unit": "iter/sec",
            "range": "stddev: 0.0015655341702423495",
            "extra": "mean: 17.110816775851255 msec\nrounds: 58"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[ethanol_1000]",
            "value": 4.839745000353749,
            "unit": "iter/sec",
            "range": "stddev: 0.07575783821226656",
            "extra": "mean: 206.62245633332077 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[periodic_100]",
            "value": 44.43390143162603,
            "unit": "iter/sec",
            "range": "stddev: 0.0010336086549478094",
            "extra": "mean: 22.50533866666602 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[periodic_1000]",
            "value": 4.21467902572453,
            "unit": "iter/sec",
            "range": "stddev: 0.016856780503876633",
            "extra": "mean: 237.26599199997054 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[ethanol_100]",
            "value": 2.181020969005931,
            "unit": "iter/sec",
            "range": "stddev: 0.0008810481656330769",
            "extra": "mean: 458.5008646000233 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[ethanol_1000]",
            "value": 0.2172659992622615,
            "unit": "iter/sec",
            "range": "stddev: 0.01631316547884803",
            "extra": "mean: 4.602652984799988 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[periodic_100]",
            "value": 2.4515430405124072,
            "unit": "iter/sec",
            "range": "stddev: 0.001077060541113543",
            "extra": "mean: 407.90636080000695 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[periodic_1000]",
            "value": 0.2387990664468627,
            "unit": "iter/sec",
            "range": "stddev: 0.08003973412830538",
            "extra": "mean: 4.187621060999914 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[ethanol_100]",
            "value": 18.245893657190738,
            "unit": "iter/sec",
            "range": "stddev: 0.001449046262976792",
            "extra": "mean: 54.806852368445014 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[ethanol_1000]",
            "value": 1.824288013325906,
            "unit": "iter/sec",
            "range": "stddev: 0.014011107488228584",
            "extra": "mean: 548.1590586000038 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[periodic_100]",
            "value": 18.3285719706732,
            "unit": "iter/sec",
            "range": "stddev: 0.0021466586624565407",
            "extra": "mean: 54.55962426314823 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[periodic_1000]",
            "value": 1.8248369520956806,
            "unit": "iter/sec",
            "range": "stddev: 0.0029691584437103956",
            "extra": "mean: 547.9941640000106 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 1565.4182289819298,
            "unit": "iter/sec",
            "range": "stddev: 0.0003561777167217086",
            "extra": "mean: 638.8069216814667 usec\nrounds: 881"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 189.57429292144698,
            "unit": "iter/sec",
            "range": "stddev: 0.006229589947316565",
            "extra": "mean: 5.274976815629561 msec\nrounds: 179"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[periodic_100]",
            "value": 984.7044886082432,
            "unit": "iter/sec",
            "range": "stddev: 0.0022458178757143138",
            "extra": "mean: 1.0155330980702395 msec\nrounds: 724"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 101.88202622653107,
            "unit": "iter/sec",
            "range": "stddev: 0.010775602618539687",
            "extra": "mean: 9.815273969684657 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[ethanol_100]",
            "value": 706.339962930765,
            "unit": "iter/sec",
            "range": "stddev: 0.00006607447394202812",
            "extra": "mean: 1.4157488638343112 msec\nrounds: 683"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 97.58798376535972,
            "unit": "iter/sec",
            "range": "stddev: 0.00040446289222417965",
            "extra": "mean: 10.247163240962095 msec\nrounds: 83"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[periodic_100]",
            "value": 705.5514180895665,
            "unit": "iter/sec",
            "range": "stddev: 0.00011991494153674195",
            "extra": "mean: 1.41733114605271 msec\nrounds: 671"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[periodic_1000]",
            "value": 98.78522826810688,
            "unit": "iter/sec",
            "range": "stddev: 0.00038148307579351985",
            "extra": "mean: 10.122970990014437 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[ethanol_100]",
            "value": 4690.5061026415715,
            "unit": "iter/sec",
            "range": "stddev: 0.000017448272806998996",
            "extra": "mean: 213.19660994297095 usec\nrounds: 3279"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 2262.4492779605566,
            "unit": "iter/sec",
            "range": "stddev: 0.000016934642218105367",
            "extra": "mean: 441.9988592634579 usec\nrounds: 1954"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[periodic_100]",
            "value": 4728.78529514625,
            "unit": "iter/sec",
            "range": "stddev: 0.000011769762864265988",
            "extra": "mean: 211.4707980136942 usec\nrounds: 3728"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[periodic_1000]",
            "value": 2267.7848798876157,
            "unit": "iter/sec",
            "range": "stddev: 0.00003149710061054997",
            "extra": "mean: 440.958932599267 usec\nrounds: 1988"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 305.32289807614234,
            "unit": "iter/sec",
            "range": "stddev: 0.00006328629065578701",
            "extra": "mean: 3.2752211062486936 msec\nrounds: 160"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 38.63668339655049,
            "unit": "iter/sec",
            "range": "stddev: 0.0003127261468666802",
            "extra": "mean: 25.882138736817165 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[periodic_100]",
            "value": 305.19749533697427,
            "unit": "iter/sec",
            "range": "stddev: 0.00008042280138213419",
            "extra": "mean: 3.2765668633547644 msec\nrounds: 161"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 38.2436021850171,
            "unit": "iter/sec",
            "range": "stddev: 0.0006494659834018524",
            "extra": "mean: 26.148164473684837 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[ethanol_100]",
            "value": 481.64275022212814,
            "unit": "iter/sec",
            "range": "stddev: 0.00008849303936306509",
            "extra": "mean: 2.0762276594816624 msec\nrounds: 464"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[ethanol_1000]",
            "value": 73.12638651102208,
            "unit": "iter/sec",
            "range": "stddev: 0.0002220268872820426",
            "extra": "mean: 13.674954386666892 msec\nrounds: 75"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[periodic_100]",
            "value": 489.62732717558856,
            "unit": "iter/sec",
            "range": "stddev: 0.00006820017576234944",
            "extra": "mean: 2.0423696646355345 msec\nrounds: 492"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[periodic_1000]",
            "value": 72.78780350575337,
            "unit": "iter/sec",
            "range": "stddev: 0.0005631347730497401",
            "extra": "mean: 13.738565416676666 msec\nrounds: 72"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[ethanol_100]",
            "value": 14.647355562077603,
            "unit": "iter/sec",
            "range": "stddev: 0.006063394778469978",
            "extra": "mean: 68.27170923528523 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[ethanol_1000]",
            "value": 1.5087582681189278,
            "unit": "iter/sec",
            "range": "stddev: 0.013313796044371442",
            "extra": "mean: 662.7966992000438 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[periodic_100]",
            "value": 11.068787866595443,
            "unit": "iter/sec",
            "range": "stddev: 0.0027311688958730853",
            "extra": "mean: 90.34412909998082 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[periodic_1000]",
            "value": 1.0705272700507498,
            "unit": "iter/sec",
            "range": "stddev: 0.034841180330639585",
            "extra": "mean: 934.1191279999748 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[ethanol_100]",
            "value": 5.478472899091207,
            "unit": "iter/sec",
            "range": "stddev: 0.006659013423736261",
            "extra": "mean: 182.5326178333171 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[ethanol_1000]",
            "value": 0.5007583468881684,
            "unit": "iter/sec",
            "range": "stddev: 0.04086156058767754",
            "extra": "mean: 1.9969712062000327 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[periodic_100]",
            "value": 5.9474547747134245,
            "unit": "iter/sec",
            "range": "stddev: 0.0036877073505705094",
            "extra": "mean: 168.13915160005308 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[periodic_1000]",
            "value": 0.5013130829413363,
            "unit": "iter/sec",
            "range": "stddev: 0.0871460710166018",
            "extra": "mean: 1.994761425600018 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 199.91722926952116,
            "unit": "iter/sec",
            "range": "stddev: 0.0004154344877940718",
            "extra": "mean: 5.002070124990759 msec\nrounds: 152"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 18.35012169145488,
            "unit": "iter/sec",
            "range": "stddev: 0.02951040586952838",
            "extra": "mean: 54.49555140910434 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[periodic_100]",
            "value": 210.9495908064483,
            "unit": "iter/sec",
            "range": "stddev: 0.0013431751020623202",
            "extra": "mean: 4.740469020001683 msec\nrounds: 200"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 23.955003712577536,
            "unit": "iter/sec",
            "range": "stddev: 0.00316033826597528",
            "extra": "mean: 41.74493195653114 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[ethanol_100]",
            "value": 10.311498579484502,
            "unit": "iter/sec",
            "range": "stddev: 0.0022218461631801217",
            "extra": "mean: 96.97911436360714 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 1.8389186836256621,
            "unit": "iter/sec",
            "range": "stddev: 0.001959239635435702",
            "extra": "mean: 543.7978355999803 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[periodic_100]",
            "value": 6.2762418131941,
            "unit": "iter/sec",
            "range": "stddev: 0.002197652858657824",
            "extra": "mean: 159.3310184285396 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[periodic_1000]",
            "value": 0.7941805178550315,
            "unit": "iter/sec",
            "range": "stddev: 0.07512156542080618",
            "extra": "mean: 1.2591595707999204 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[ethanol_100]",
            "value": 25.678185583691498,
            "unit": "iter/sec",
            "range": "stddev: 0.0002747185823779081",
            "extra": "mean: 38.94356151998181 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 2.904930649527181,
            "unit": "iter/sec",
            "range": "stddev: 0.026056506731495246",
            "extra": "mean: 344.24229720002586 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[periodic_100]",
            "value": 42.00508051453104,
            "unit": "iter/sec",
            "range": "stddev: 0.0004335699083615491",
            "extra": "mean: 23.806644047594784 msec\nrounds: 42"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[periodic_1000]",
            "value": 5.392840349743349,
            "unit": "iter/sec",
            "range": "stddev: 0.0006416374633121743",
            "extra": "mean: 185.43104100005317 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 58.76788550335696,
            "unit": "iter/sec",
            "range": "stddev: 0.0018740988375250834",
            "extra": "mean: 17.016096315782498 msec\nrounds: 38"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 14.306813911002815,
            "unit": "iter/sec",
            "range": "stddev: 0.03603565568700885",
            "extra": "mean: 69.89676431248881 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[periodic_100]",
            "value": 46.89276444456799,
            "unit": "iter/sec",
            "range": "stddev: 0.020447197254915842",
            "extra": "mean: 21.32525160000114 msec\nrounds: 55"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 13.721583664797873,
            "unit": "iter/sec",
            "range": "stddev: 0.035454000918380885",
            "extra": "mean: 72.87788526665888 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[ethanol_100]",
            "value": 130.04098599290626,
            "unit": "iter/sec",
            "range": "stddev: 0.0021359725720987714",
            "extra": "mean: 7.689883249997428 msec\nrounds: 116"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[ethanol_1000]",
            "value": 15.708448247329978,
            "unit": "iter/sec",
            "range": "stddev: 0.002225465296652617",
            "extra": "mean: 63.66001175004499 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[periodic_100]",
            "value": 130.19424705002035,
            "unit": "iter/sec",
            "range": "stddev: 0.0015339867133988424",
            "extra": "mean: 7.680830932689385 msec\nrounds: 104"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[periodic_1000]",
            "value": 14.152243537390246,
            "unit": "iter/sec",
            "range": "stddev: 0.035638720122566865",
            "extra": "mean: 70.66017464707971 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[ethanol_100]",
            "value": 9.024200338565612,
            "unit": "iter/sec",
            "range": "stddev: 0.0029137991167880644",
            "extra": "mean: 110.81314271431049 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[ethanol_1000]",
            "value": 0.9030282339879284,
            "unit": "iter/sec",
            "range": "stddev: 0.02066954921887903",
            "extra": "mean: 1.107385087600005 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[periodic_100]",
            "value": 6.6749209947558175,
            "unit": "iter/sec",
            "range": "stddev: 0.005104447270989468",
            "extra": "mean: 149.81450728565247 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[periodic_1000]",
            "value": 0.6682311576076806,
            "unit": "iter/sec",
            "range": "stddev: 0.06327900298888403",
            "extra": "mean: 1.4964881367999623 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[ethanol_100]",
            "value": 55.47947243763452,
            "unit": "iter/sec",
            "range": "stddev: 0.00011964367852754903",
            "extra": "mean: 18.024684735856457 msec\nrounds: 53"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[ethanol_1000]",
            "value": 19.082788061658974,
            "unit": "iter/sec",
            "range": "stddev: 0.0004774461607809737",
            "extra": "mean: 52.403244052644176 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[periodic_100]",
            "value": 54.07592606101738,
            "unit": "iter/sec",
            "range": "stddev: 0.00015864681376345796",
            "extra": "mean: 18.49251733334414 msec\nrounds: 54"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[periodic_1000]",
            "value": 13.092074161729625,
            "unit": "iter/sec",
            "range": "stddev: 0.0006732389033363431",
            "extra": "mean: 76.38209100000145 msec\nrounds: 13"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[ethanol_100]",
            "value": 50.74259354235493,
            "unit": "iter/sec",
            "range": "stddev: 0.00020271356636555765",
            "extra": "mean: 19.707309583324673 msec\nrounds: 48"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[ethanol_1000]",
            "value": 5.056959437682511,
            "unit": "iter/sec",
            "range": "stddev: 0.0034446424786470256",
            "extra": "mean: 197.74728516673198 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[periodic_100]",
            "value": 33.86364296205864,
            "unit": "iter/sec",
            "range": "stddev: 0.00015615352759207435",
            "extra": "mean: 29.530195588242403 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[periodic_1000]",
            "value": 3.1553937385508113,
            "unit": "iter/sec",
            "range": "stddev: 0.02763599717167691",
            "extra": "mean: 316.9176599999446 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[ethanol_100]",
            "value": 4.378302667536962,
            "unit": "iter/sec",
            "range": "stddev: 0.012405229874090594",
            "extra": "mean: 228.3990112000538 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[ethanol_1000]",
            "value": 0.40902450536801865,
            "unit": "iter/sec",
            "range": "stddev: 0.19985368370359693",
            "extra": "mean: 2.4448412916000053 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[periodic_100]",
            "value": 4.230940190695201,
            "unit": "iter/sec",
            "range": "stddev: 0.010722452556044862",
            "extra": "mean: 236.35408559998723 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[periodic_1000]",
            "value": 0.4221174632432915,
            "unit": "iter/sec",
            "range": "stddev: 0.06841226844687678",
            "extra": "mean: 2.369008835400018 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[ethanol_100]",
            "value": 164.32423498684977,
            "unit": "iter/sec",
            "range": "stddev: 0.0008474602409968417",
            "extra": "mean: 6.085529624282298 msec\nrounds: 173"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[ethanol_1000]",
            "value": 147.74674289892033,
            "unit": "iter/sec",
            "range": "stddev: 0.001284078587322648",
            "extra": "mean: 6.768338715149488 msec\nrounds: 165"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[periodic_100]",
            "value": 141.8153911056822,
            "unit": "iter/sec",
            "range": "stddev: 0.0009974074127214224",
            "extra": "mean: 7.05142080985265 msec\nrounds: 142"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[periodic_1000]",
            "value": 155.02814151206854,
            "unit": "iter/sec",
            "range": "stddev: 0.0011174120063033263",
            "extra": "mean: 6.4504417729999854 msec\nrounds: 163"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[ethanol_100]",
            "value": 1.9276789020593987,
            "unit": "iter/sec",
            "range": "stddev: 0.004140982219168669",
            "extra": "mean: 518.7585955999566 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[ethanol_1000]",
            "value": 1.9281113077246044,
            "unit": "iter/sec",
            "range": "stddev: 0.003520695357778702",
            "extra": "mean: 518.642256800058 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[periodic_100]",
            "value": 2.1125422383913706,
            "unit": "iter/sec",
            "range": "stddev: 0.029480717968263653",
            "extra": "mean: 473.36331639999116 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[periodic_1000]",
            "value": 2.1364420404067417,
            "unit": "iter/sec",
            "range": "stddev: 0.023125647491871768",
            "extra": "mean: 468.0679284000689 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[ethanol_100]",
            "value": 18.653672154744072,
            "unit": "iter/sec",
            "range": "stddev: 0.0017891370754186818",
            "extra": "mean: 53.60874747365367 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[ethanol_1000]",
            "value": 18.78319205672293,
            "unit": "iter/sec",
            "range": "stddev: 0.0004950358471988589",
            "extra": "mean: 53.23908721052967 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[periodic_100]",
            "value": 21.71636561077008,
            "unit": "iter/sec",
            "range": "stddev: 0.0001550123489351748",
            "extra": "mean: 46.04822086362633 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[periodic_1000]",
            "value": 21.5490144464661,
            "unit": "iter/sec",
            "range": "stddev: 0.0005412357722948719",
            "extra": "mean: 46.40583459091762 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[ethanol_100]",
            "value": 37.28462319917991,
            "unit": "iter/sec",
            "range": "stddev: 0.0011483189261812072",
            "extra": "mean: 26.820708222203393 msec\nrounds: 27"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[ethanol_1000]",
            "value": 34.35688100410448,
            "unit": "iter/sec",
            "range": "stddev: 0.0033520662535304023",
            "extra": "mean: 29.106250939383408 msec\nrounds: 33"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[periodic_100]",
            "value": 37.044156519517806,
            "unit": "iter/sec",
            "range": "stddev: 0.001032556312777205",
            "extra": "mean: 26.994810894752607 msec\nrounds: 38"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[periodic_1000]",
            "value": 36.9053354852117,
            "unit": "iter/sec",
            "range": "stddev: 0.0009161511594627737",
            "extra": "mean: 27.096353057153728 msec\nrounds: 35"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[ethanol_100]",
            "value": 165.21064190960746,
            "unit": "iter/sec",
            "range": "stddev: 0.00037422467745720805",
            "extra": "mean: 6.052878848731398 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[ethanol_1000]",
            "value": 171.20417620720423,
            "unit": "iter/sec",
            "range": "stddev: 0.00022230858271582324",
            "extra": "mean: 5.840979012040713 msec\nrounds: 166"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[periodic_100]",
            "value": 170.84470014728893,
            "unit": "iter/sec",
            "range": "stddev: 0.00038686482621844343",
            "extra": "mean: 5.853269075001322 msec\nrounds: 160"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[periodic_1000]",
            "value": 172.74376142375942,
            "unit": "iter/sec",
            "range": "stddev: 0.00022497435647647517",
            "extra": "mean: 5.788921068743491 msec\nrounds: 160"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[ethanol_100]",
            "value": 76.34364789754859,
            "unit": "iter/sec",
            "range": "stddev: 0.004581557526764646",
            "extra": "mean: 13.098666720012867 msec\nrounds: 75"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[ethanol_1000]",
            "value": 81.85988868736139,
            "unit": "iter/sec",
            "range": "stddev: 0.0006161997552631922",
            "extra": "mean: 12.215995111100037 msec\nrounds: 81"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[periodic_100]",
            "value": 70.95368349310364,
            "unit": "iter/sec",
            "range": "stddev: 0.004416090103898181",
            "extra": "mean: 14.093700999993823 msec\nrounds: 76"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[periodic_1000]",
            "value": 65.26809596746007,
            "unit": "iter/sec",
            "range": "stddev: 0.002897489496251293",
            "extra": "mean: 15.321421364866502 msec\nrounds: 74"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[ethanol_100]",
            "value": 10.413314802081201,
            "unit": "iter/sec",
            "range": "stddev: 0.01015856123955767",
            "extra": "mean: 96.03090072722478 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[ethanol_1000]",
            "value": 11.009090999096092,
            "unit": "iter/sec",
            "range": "stddev: 0.00045539349430962086",
            "extra": "mean: 90.83402072724311 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[periodic_100]",
            "value": 13.134227771868645,
            "unit": "iter/sec",
            "range": "stddev: 0.00027505623088139243",
            "extra": "mean: 76.13694671428155 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[periodic_1000]",
            "value": 13.00889679938673,
            "unit": "iter/sec",
            "range": "stddev: 0.0011591220864201092",
            "extra": "mean: 76.8704691428671 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[ethanol_100]",
            "value": 380.6462414375726,
            "unit": "iter/sec",
            "range": "stddev: 0.00005355555455441369",
            "extra": "mean: 2.627111189180108 msec\nrounds: 333"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[ethanol_1000]",
            "value": 381.19436477242675,
            "unit": "iter/sec",
            "range": "stddev: 0.00003753397915827635",
            "extra": "mean: 2.623333638725222 msec\nrounds: 346"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[periodic_100]",
            "value": 276.2224050678524,
            "unit": "iter/sec",
            "range": "stddev: 0.00010704546289618376",
            "extra": "mean: 3.620271135335151 msec\nrounds: 266"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[periodic_1000]",
            "value": 277.78381564562795,
            "unit": "iter/sec",
            "range": "stddev: 0.000034956556529067576",
            "extra": "mean: 3.599921750933509 msec\nrounds: 269"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[ethanol_100]",
            "value": 33.65218280806591,
            "unit": "iter/sec",
            "range": "stddev: 0.002058328505585456",
            "extra": "mean: 29.71575441936312 msec\nrounds: 31"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[ethanol_1000]",
            "value": 31.337993996183577,
            "unit": "iter/sec",
            "range": "stddev: 0.003829110386154309",
            "extra": "mean: 31.910147156253288 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[periodic_100]",
            "value": 32.32963073399522,
            "unit": "iter/sec",
            "range": "stddev: 0.0015270651146966985",
            "extra": "mean: 30.93137710813632 msec\nrounds: 37"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[periodic_1000]",
            "value": 32.52888455533729,
            "unit": "iter/sec",
            "range": "stddev: 0.0019025933669943635",
            "extra": "mean: 30.741908727267486 msec\nrounds: 33"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_encode_current",
            "value": 44692.25364918442,
            "unit": "iter/sec",
            "range": "stddev: 0.000002478275911443926",
            "extra": "mean: 22.375242203035533 usec\nrounds: 11350"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_atoms_to_dict_new",
            "value": 239364.79263943326,
            "unit": "iter/sec",
            "range": "stddev: 7.391611865890588e-7",
            "extra": "mean: 4.177723837215895 usec\nrounds: 32651"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_decode_current",
            "value": 45184.559509289196,
            "unit": "iter/sec",
            "range": "stddev: 0.00004168917701175483",
            "extra": "mean: 22.131453993579743 usec\nrounds: 12205"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_dict_to_atoms_new",
            "value": 164344.40430895155,
            "unit": "iter/sec",
            "range": "stddev: 0.000016128300959819903",
            "extra": "mean: 6.084782771916572 usec\nrounds: 54933"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_read_current_aseio",
            "value": 23.017442769488497,
            "unit": "iter/sec",
            "range": "stddev: 0.046868889551435006",
            "extra": "mean: 43.44531275757453 msec\nrounds: 33"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_read_new_aseio",
            "value": 21.956282136295457,
            "unit": "iter/sec",
            "range": "stddev: 0.047014754089082025",
            "extra": "mean: 45.54505147057304 msec\nrounds: 34"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_write_current_aseio",
            "value": 30.835919260137644,
            "unit": "iter/sec",
            "range": "stddev: 0.0007409469930772406",
            "extra": "mean: 32.42971262065551 msec\nrounds: 29"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_write_new_aseio",
            "value": 31.432757776448568,
            "unit": "iter/sec",
            "range": "stddev: 0.0016541736807130275",
            "extra": "mean: 31.813944137897565 msec\nrounds: 29"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_random_access_current",
            "value": 22.01191036351273,
            "unit": "iter/sec",
            "range": "stddev: 0.05391276258065246",
            "extra": "mean: 45.42995058064633 msec\nrounds: 31"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_random_access_new",
            "value": 22.048241022178924,
            "unit": "iter/sec",
            "range": "stddev: 0.050248853196096156",
            "extra": "mean: 45.35509200004086 msec\nrounds: 31"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_via_view",
            "value": 120.29984557347412,
            "unit": "iter/sec",
            "range": "stddev: 0.016301789355852733",
            "extra": "mean: 8.312562624107791 msec\nrounds: 141"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_manual_loop",
            "value": 36.533856415482894,
            "unit": "iter/sec",
            "range": "stddev: 0.0002852945319366484",
            "extra": "mean: 27.371870864861783 msec\nrounds: 37"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_selective_keys",
            "value": 881.4601898696526,
            "unit": "iter/sec",
            "range": "stddev: 0.00002079510863562542",
            "extra": "mean: 1.1344811841676896 msec\nrounds: 619"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_row_view_iteration",
            "value": 24.100554597965157,
            "unit": "iter/sec",
            "range": "stddev: 0.044741716631799565",
            "extra": "mean: 41.492821085720216 msec\nrounds: 35"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_direct_iteration",
            "value": 25.694744702255704,
            "unit": "iter/sec",
            "range": "stddev: 0.0337842989371236",
            "extra": "mean: 38.918464129056375 msec\nrounds: 31"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_multi_column_view",
            "value": 93.09336165387879,
            "unit": "iter/sec",
            "range": "stddev: 0.0014340858432046741",
            "extra": "mean: 10.741904494952077 msec\nrounds: 99"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_multi_column_manual",
            "value": 36.335004783578256,
            "unit": "iter/sec",
            "range": "stddev: 0.00047056009999273097",
            "extra": "mean: 27.52166969445271 msec\nrounds: 36"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[ethanol_100]",
            "value": 200.65072165250467,
            "unit": "iter/sec",
            "range": "stddev: 0.0023189560798476273",
            "extra": "mean: 4.983784716866565 msec\nrounds: 166"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[ethanol_1000]",
            "value": 18.547024029890057,
            "unit": "iter/sec",
            "range": "stddev: 0.04332659699191096",
            "extra": "mean: 53.91700568179658 msec\nrounds: 22"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[periodic_100]",
            "value": 208.58056840235014,
            "unit": "iter/sec",
            "range": "stddev: 0.0008204297038216613",
            "extra": "mean: 4.7943104559529655 msec\nrounds: 193"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[periodic_1000]",
            "value": 19.927645422700316,
            "unit": "iter/sec",
            "range": "stddev: 0.0303932841341611",
            "extra": "mean: 50.181543217387 msec\nrounds: 23"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[ethanol_100]",
            "value": 10.213510943973032,
            "unit": "iter/sec",
            "range": "stddev: 0.0006576499454943761",
            "extra": "mean: 97.90952450000532 msec\nrounds: 10"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[ethanol_1000]",
            "value": 1.7513443879075874,
            "unit": "iter/sec",
            "range": "stddev: 0.03717168613482754",
            "extra": "mean: 570.9899246000077 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[periodic_100]",
            "value": 6.170806013367655,
            "unit": "iter/sec",
            "range": "stddev: 0.0038219535637699182",
            "extra": "mean: 162.05338457143625 msec\nrounds: 7"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[periodic_1000]",
            "value": 0.7626303928991823,
            "unit": "iter/sec",
            "range": "stddev: 0.06018560359943024",
            "extra": "mean: 1.3112511766000352 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[ethanol_100]",
            "value": 25.447989241023148,
            "unit": "iter/sec",
            "range": "stddev: 0.0010925707663282356",
            "extra": "mean: 39.295835538470016 msec\nrounds: 26"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[ethanol_1000]",
            "value": 3.0420958716632107,
            "unit": "iter/sec",
            "range": "stddev: 0.0037832917707636667",
            "extra": "mean: 328.7207380000382 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[periodic_100]",
            "value": 41.77249400639494,
            "unit": "iter/sec",
            "range": "stddev: 0.0003625892415693477",
            "extra": "mean: 23.93919788095272 msec\nrounds: 42"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[periodic_1000]",
            "value": 5.371560124517477,
            "unit": "iter/sec",
            "range": "stddev: 0.0035515163542576265",
            "extra": "mean: 186.16565333331891 msec\nrounds: 6"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[ethanol_100]",
            "value": 9.169798917998259,
            "unit": "iter/sec",
            "range": "stddev: 0.004549406692645321",
            "extra": "mean: 109.05364544441909 msec\nrounds: 9"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[ethanol_1000]",
            "value": 0.8988179224315885,
            "unit": "iter/sec",
            "range": "stddev: 0.03202403270277265",
            "extra": "mean: 1.1125723854000171 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[periodic_100]",
            "value": 7.014813588714163,
            "unit": "iter/sec",
            "range": "stddev: 0.0018817600127531986",
            "extra": "mean: 142.55546314286352 msec\nrounds: 7"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[periodic_1000]",
            "value": 0.6763928641700324,
            "unit": "iter/sec",
            "range": "stddev: 0.041386078200606226",
            "extra": "mean: 1.4784307359999276 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[ethanol_100]",
            "value": 54.642696477974816,
            "unit": "iter/sec",
            "range": "stddev: 0.0003632195365954521",
            "extra": "mean: 18.30070740383532 msec\nrounds: 52"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[ethanol_1000]",
            "value": 19.009699166736944,
            "unit": "iter/sec",
            "range": "stddev: 0.0004335777490782264",
            "extra": "mean: 52.60472515787067 msec\nrounds: 19"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[periodic_100]",
            "value": 50.712712199276,
            "unit": "iter/sec",
            "range": "stddev: 0.002081278612559865",
            "extra": "mean: 19.718921679252574 msec\nrounds: 53"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[periodic_1000]",
            "value": 12.72586997331455,
            "unit": "iter/sec",
            "range": "stddev: 0.0028535725420524823",
            "extra": "mean: 78.58008938461143 msec\nrounds: 13"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[ethanol_100]",
            "value": 50.39702339298525,
            "unit": "iter/sec",
            "range": "stddev: 0.00017196916958229458",
            "extra": "mean: 19.84244172919129 msec\nrounds: 48"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[ethanol_1000]",
            "value": 5.082552761796604,
            "unit": "iter/sec",
            "range": "stddev: 0.0003872048275026445",
            "extra": "mean: 196.7515236667244 msec\nrounds: 6"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[periodic_100]",
            "value": 33.42565949535237,
            "unit": "iter/sec",
            "range": "stddev: 0.00017209777208936896",
            "extra": "mean: 29.91713596971942 msec\nrounds: 33"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[periodic_1000]",
            "value": 3.3457713767184583,
            "unit": "iter/sec",
            "range": "stddev: 0.00257529426341772",
            "extra": "mean: 298.88473759997396 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[ethanol_100]",
            "value": 4.467094148457775,
            "unit": "iter/sec",
            "range": "stddev: 0.007871104088240724",
            "extra": "mean: 223.85917259998678 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[ethanol_1000]",
            "value": 0.42825005168496966,
            "unit": "iter/sec",
            "range": "stddev: 0.06511033753823368",
            "extra": "mean: 2.335084364999966 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[periodic_100]",
            "value": 4.610445208527295,
            "unit": "iter/sec",
            "range": "stddev: 0.003300152977683298",
            "extra": "mean: 216.89879279997513 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[periodic_1000]",
            "value": 0.4280177114622836,
            "unit": "iter/sec",
            "range": "stddev: 0.04711930356690222",
            "extra": "mean: 2.336351915399928 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "name": "Fabian Zills",
            "username": "PythonFZ",
            "email": "46721498+PythonFZ@users.noreply.github.com"
          },
          "committer": {
            "name": "GitHub",
            "username": "web-flow",
            "email": "noreply@github.com"
          },
          "id": "cd81592cf0e195a2bcba16b5dec612a1e0f5cf6d",
          "message": "build: switch to hatchling + hatch-vcs and add PyPI publish workflow (#15)\n\nReplace uv_build with hatchling/hatch-vcs for automatic git-tag versioning.\nAdd GitHub Actions workflow for publishing to PyPI on release via trusted publishing.\n\nCo-authored-by: Claude Opus 4.6 <noreply@anthropic.com>",
          "timestamp": "2026-03-10T14:29:08Z",
          "url": "https://github.com/zincware/asebytes/commit/cd81592cf0e195a2bcba16b5dec612a1e0f5cf6d"
        },
        "date": 1773153439501,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 3532.1375424264024,
            "unit": "iter/sec",
            "range": "stddev: 0.00001357038119444905",
            "extra": "mean: 283.11468281981166 usec\nrounds: 2043"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 341.02785699626565,
            "unit": "iter/sec",
            "range": "stddev: 0.000045309869636931324",
            "extra": "mean: 2.9323117730260675 msec\nrounds: 304"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[periodic_100]",
            "value": 3354.7791801761005,
            "unit": "iter/sec",
            "range": "stddev: 0.00003366193565113692",
            "extra": "mean: 298.08221235816404 usec\nrounds: 2557"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 332.5483493138039,
            "unit": "iter/sec",
            "range": "stddev: 0.000046211159153367435",
            "extra": "mean: 3.007081532846119 msec\nrounds: 274"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[ethanol_100]",
            "value": 127.65298956977664,
            "unit": "iter/sec",
            "range": "stddev: 0.000574907250860505",
            "extra": "mean: 7.833737410853102 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 14.043120229207592,
            "unit": "iter/sec",
            "range": "stddev: 0.0024691222846217713",
            "extra": "mean: 71.20924578571574 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[periodic_100]",
            "value": 48.6860116770329,
            "unit": "iter/sec",
            "range": "stddev: 0.0004312211757431286",
            "extra": "mean: 20.539780638300652 msec\nrounds: 47"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[periodic_1000]",
            "value": 4.613493074706873,
            "unit": "iter/sec",
            "range": "stddev: 0.01970794786833386",
            "extra": "mean: 216.75550039999507 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[ethanol_100]",
            "value": 1917.168235157055,
            "unit": "iter/sec",
            "range": "stddev: 0.00003488025572881019",
            "extra": "mean: 521.6026333328434 usec\nrounds: 1140"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 228.71502264384876,
            "unit": "iter/sec",
            "range": "stddev: 0.00033466401850417",
            "extra": "mean: 4.372253245285 msec\nrounds: 159"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[periodic_100]",
            "value": 1810.4321900292005,
            "unit": "iter/sec",
            "range": "stddev: 0.00004433770367011056",
            "extra": "mean: 552.3542972266036 usec\nrounds: 757"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[periodic_1000]",
            "value": 211.53745497990118,
            "unit": "iter/sec",
            "range": "stddev: 0.00005646717524774484",
            "extra": "mean: 4.727295221052049 msec\nrounds: 95"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 926.0918959941017,
            "unit": "iter/sec",
            "range": "stddev: 0.00003860109105295017",
            "extra": "mean: 1.0798064472063678 msec\nrounds: 161"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 247.35612208158088,
            "unit": "iter/sec",
            "range": "stddev: 0.00007823216454718595",
            "extra": "mean: 4.042754194174295 msec\nrounds: 103"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[periodic_100]",
            "value": 926.9381635276344,
            "unit": "iter/sec",
            "range": "stddev: 0.00004410905866064612",
            "extra": "mean: 1.0788206153842188 msec\nrounds: 169"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 246.39011342433028,
            "unit": "iter/sec",
            "range": "stddev: 0.00011948869908772955",
            "extra": "mean: 4.0586044062482785 msec\nrounds: 96"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[ethanol_100]",
            "value": 331.16684760301547,
            "unit": "iter/sec",
            "range": "stddev: 0.00034372353608557766",
            "extra": "mean: 3.0196259294612267 msec\nrounds: 241"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[ethanol_1000]",
            "value": 49.042718482541225,
            "unit": "iter/sec",
            "range": "stddev: 0.00018897825971707707",
            "extra": "mean: 20.390386808512485 msec\nrounds: 47"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[periodic_100]",
            "value": 338.61540915317266,
            "unit": "iter/sec",
            "range": "stddev: 0.0000827279578309364",
            "extra": "mean: 2.9532028755007134 msec\nrounds: 249"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[periodic_1000]",
            "value": 47.959006738455095,
            "unit": "iter/sec",
            "range": "stddev: 0.00022802148157369172",
            "extra": "mean: 20.851140755552127 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[ethanol_100]",
            "value": 145.85412082118495,
            "unit": "iter/sec",
            "range": "stddev: 0.0003566939945738743",
            "extra": "mean: 6.85616556028599 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[ethanol_1000]",
            "value": 14.354720164660941,
            "unit": "iter/sec",
            "range": "stddev: 0.003881535919747804",
            "extra": "mean: 69.66349664285636 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[periodic_100]",
            "value": 89.13160186760017,
            "unit": "iter/sec",
            "range": "stddev: 0.00011589476126674283",
            "extra": "mean: 11.219365287358372 msec\nrounds: 87"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[periodic_1000]",
            "value": 8.872651507238057,
            "unit": "iter/sec",
            "range": "stddev: 0.0004823562790052347",
            "extra": "mean: 112.70588044444531 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[ethanol_100]",
            "value": 1658.575724911798,
            "unit": "iter/sec",
            "range": "stddev: 0.000016925935699287303",
            "extra": "mean: 602.9269480916702 usec\nrounds: 1310"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[ethanol_1000]",
            "value": 238.5937179401617,
            "unit": "iter/sec",
            "range": "stddev: 0.01334810281373404",
            "extra": "mean: 4.191225186619523 msec\nrounds: 284"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[periodic_100]",
            "value": 681.4213484278779,
            "unit": "iter/sec",
            "range": "stddev: 0.006235300787454197",
            "extra": "mean: 1.4675207965044268 msec\nrounds: 801"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[periodic_1000]",
            "value": 118.12404819702729,
            "unit": "iter/sec",
            "range": "stddev: 0.011976556467208917",
            "extra": "mean: 8.465676678571247 msec\nrounds: 112"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[ethanol_100]",
            "value": 49.96528331981563,
            "unit": "iter/sec",
            "range": "stddev: 0.00301565044804531",
            "extra": "mean: 20.013896320756217 msec\nrounds: 53"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[ethanol_1000]",
            "value": 5.536430882935487,
            "unit": "iter/sec",
            "range": "stddev: 0.0005387820690919767",
            "extra": "mean: 180.62177983332597 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[periodic_100]",
            "value": 54.04495934293455,
            "unit": "iter/sec",
            "range": "stddev: 0.00014893249470332478",
            "extra": "mean: 18.503113188681358 msec\nrounds: 53"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[periodic_1000]",
            "value": 5.490827404435668,
            "unit": "iter/sec",
            "range": "stddev: 0.0009175614111636501",
            "extra": "mean: 182.12191466666164 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[ethanol_100]",
            "value": 353.7502657548622,
            "unit": "iter/sec",
            "range": "stddev: 0.0006920541630324175",
            "extra": "mean: 2.8268530000001992 msec\nrounds: 363"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[ethanol_1000]",
            "value": 37.79760403574301,
            "unit": "iter/sec",
            "range": "stddev: 0.0003223893524048489",
            "extra": "mean: 26.45670342105171 msec\nrounds: 38"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[periodic_100]",
            "value": 417.19855515510875,
            "unit": "iter/sec",
            "range": "stddev: 0.0000981694298588559",
            "extra": "mean: 2.3969402282043224 msec\nrounds: 390"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[periodic_1000]",
            "value": 40.62408094364595,
            "unit": "iter/sec",
            "range": "stddev: 0.0002664667976985956",
            "extra": "mean: 24.615941499998684 msec\nrounds: 40"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[ethanol_100]",
            "value": 1.3967661065429662,
            "unit": "iter/sec",
            "range": "stddev: 0.015712065529983575",
            "extra": "mean: 715.939480000003 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[ethanol_1000]",
            "value": 0.13800067514346298,
            "unit": "iter/sec",
            "range": "stddev: 0.058673922205062914",
            "extra": "mean: 7.246341360000002 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[periodic_100]",
            "value": 1.4399847070398568,
            "unit": "iter/sec",
            "range": "stddev: 0.03463342013278457",
            "extra": "mean: 694.451819599999 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[periodic_1000]",
            "value": 0.14750091880151342,
            "unit": "iter/sec",
            "range": "stddev: 0.052258631485743966",
            "extra": "mean: 6.779618785599996 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[ethanol_100]",
            "value": 11.929220973516417,
            "unit": "iter/sec",
            "range": "stddev: 0.0002193947827391198",
            "extra": "mean: 83.82777066667302 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[ethanol_1000]",
            "value": 1.1752030927107158,
            "unit": "iter/sec",
            "range": "stddev: 0.004809483313327243",
            "extra": "mean: 850.9167531999992 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[periodic_100]",
            "value": 15.470910010262264,
            "unit": "iter/sec",
            "range": "stddev: 0.0006240873476967115",
            "extra": "mean: 64.63743886666482 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[periodic_1000]",
            "value": 1.521055502686486,
            "unit": "iter/sec",
            "range": "stddev: 0.02277915841455347",
            "extra": "mean: 657.4382054000012 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[ethanol_100]",
            "value": 25.552258212238854,
            "unit": "iter/sec",
            "range": "stddev: 0.0017539365356158678",
            "extra": "mean: 39.135484296297015 msec\nrounds: 27"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.568313885014436,
            "unit": "iter/sec",
            "range": "stddev: 0.0031130273736220625",
            "extra": "mean: 389.36050840000007 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[periodic_100]",
            "value": 25.575035139557727,
            "unit": "iter/sec",
            "range": "stddev: 0.001221542559094872",
            "extra": "mean: 39.10063053846084 msec\nrounds: 26"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[periodic_1000]",
            "value": 2.54848518550269,
            "unit": "iter/sec",
            "range": "stddev: 0.002079739400741297",
            "extra": "mean: 392.3899600000027 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[ethanol_100]",
            "value": 34.44294530061576,
            "unit": "iter/sec",
            "range": "stddev: 0.003265373239315353",
            "extra": "mean: 29.033521705883913 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[ethanol_1000]",
            "value": 3.704397883171164,
            "unit": "iter/sec",
            "range": "stddev: 0.0045676034351791696",
            "extra": "mean: 269.9494037999898 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[periodic_100]",
            "value": 38.07466548319956,
            "unit": "iter/sec",
            "range": "stddev: 0.001012866888514798",
            "extra": "mean: 26.264183474999925 msec\nrounds: 40"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[periodic_1000]",
            "value": 3.779197775901414,
            "unit": "iter/sec",
            "range": "stddev: 0.0026107830548539154",
            "extra": "mean: 264.6064216000127 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[ethanol_100]",
            "value": 134.53875810555655,
            "unit": "iter/sec",
            "range": "stddev: 0.0004862881744330701",
            "extra": "mean: 7.432802369228196 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[ethanol_1000]",
            "value": 13.800123686763051,
            "unit": "iter/sec",
            "range": "stddev: 0.001027196543233464",
            "extra": "mean: 72.46311864285612 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[periodic_100]",
            "value": 84.78199814316041,
            "unit": "iter/sec",
            "range": "stddev: 0.00010809323688744083",
            "extra": "mean: 11.794956734935985 msec\nrounds: 83"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[periodic_1000]",
            "value": 8.394017995241684,
            "unit": "iter/sec",
            "range": "stddev: 0.003091294813788748",
            "extra": "mean: 119.13245844443863 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[ethanol_100]",
            "value": 2.1682812073767295,
            "unit": "iter/sec",
            "range": "stddev: 0.0024903968815720413",
            "extra": "mean: 461.1947918000169 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[ethanol_1000]",
            "value": 0.2154121975060539,
            "unit": "iter/sec",
            "range": "stddev: 0.04166207525036389",
            "extra": "mean: 4.642262655399986 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[periodic_100]",
            "value": 2.4462311770235705,
            "unit": "iter/sec",
            "range": "stddev: 0.00034351777044078127",
            "extra": "mean: 408.7921081999866 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[periodic_1000]",
            "value": 0.2399502588910519,
            "unit": "iter/sec",
            "range": "stddev: 0.028564275920741324",
            "extra": "mean: 4.1675304065999965 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[ethanol_100]",
            "value": 24.79889389077137,
            "unit": "iter/sec",
            "range": "stddev: 0.0001666843642115378",
            "extra": "mean: 40.32437915999708 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[ethanol_1000]",
            "value": 2.5175487510563945,
            "unit": "iter/sec",
            "range": "stddev: 0.0009425354530194315",
            "extra": "mean: 397.21177180000495 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[periodic_100]",
            "value": 25.155574043937772,
            "unit": "iter/sec",
            "range": "stddev: 0.00022894043604496813",
            "extra": "mean: 39.75262096000506 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[periodic_1000]",
            "value": 2.4603398360539894,
            "unit": "iter/sec",
            "range": "stddev: 0.011378497316141042",
            "extra": "mean: 406.44791639997493 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[ethanol_100]",
            "value": 9549.656998939892,
            "unit": "iter/sec",
            "range": "stddev: 0.000007952881164984587",
            "extra": "mean: 104.71580289334058 usec\nrounds: 5875"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[ethanol_1000]",
            "value": 852.7996760397292,
            "unit": "iter/sec",
            "range": "stddev: 0.00003453191540308354",
            "extra": "mean: 1.172608325373488 msec\nrounds: 670"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[periodic_100]",
            "value": 9264.661235906244,
            "unit": "iter/sec",
            "range": "stddev: 0.000009396376337612074",
            "extra": "mean: 107.93702808305464 usec\nrounds: 5555"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[periodic_1000]",
            "value": 849.6214006851894,
            "unit": "iter/sec",
            "range": "stddev: 0.00003289975040105959",
            "extra": "mean: 1.176994834632856 msec\nrounds: 641"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[ethanol_100]",
            "value": 724.1819980598506,
            "unit": "iter/sec",
            "range": "stddev: 0.00019150709327740817",
            "extra": "mean: 1.3808683489496991 msec\nrounds: 619"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[ethanol_1000]",
            "value": 99.78396034182379,
            "unit": "iter/sec",
            "range": "stddev: 0.0003315453892761513",
            "extra": "mean: 10.021650740002315 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[periodic_100]",
            "value": 733.035848880724,
            "unit": "iter/sec",
            "range": "stddev: 0.00007680220552063903",
            "extra": "mean: 1.3641897616970642 msec\nrounds: 684"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[periodic_1000]",
            "value": 100.2791129833011,
            "unit": "iter/sec",
            "range": "stddev: 0.00035482233446612523",
            "extra": "mean: 9.972166388892212 msec\nrounds: 72"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[ethanol_100]",
            "value": 3319.1470926049337,
            "unit": "iter/sec",
            "range": "stddev: 0.000016286207215827765",
            "extra": "mean: 301.2822186241767 usec\nrounds: 2470"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[ethanol_1000]",
            "value": 439.52607201005964,
            "unit": "iter/sec",
            "range": "stddev: 0.0003938481658289303",
            "extra": "mean: 2.275177887461276 msec\nrounds: 311"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[periodic_100]",
            "value": 3337.6084765187006,
            "unit": "iter/sec",
            "range": "stddev: 0.000015119924234487927",
            "extra": "mean: 299.6157299561547 usec\nrounds: 2507"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[periodic_1000]",
            "value": 475.5715985990375,
            "unit": "iter/sec",
            "range": "stddev: 0.00003393130558681139",
            "extra": "mean: 2.102732801844874 msec\nrounds: 434"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[ethanol_100]",
            "value": 930.3132876241377,
            "unit": "iter/sec",
            "range": "stddev: 0.00003124652360186405",
            "extra": "mean: 1.0749067150850122 msec\nrounds: 179"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[ethanol_1000]",
            "value": 245.81968688905218,
            "unit": "iter/sec",
            "range": "stddev: 0.00009400653429071456",
            "extra": "mean: 4.068022429999019 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[periodic_100]",
            "value": 938.11172995006,
            "unit": "iter/sec",
            "range": "stddev: 0.0000564407817254226",
            "extra": "mean: 1.065971107783968 msec\nrounds: 167"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[periodic_1000]",
            "value": 246.55882987748257,
            "unit": "iter/sec",
            "range": "stddev: 0.00008166845081420937",
            "extra": "mean: 4.055827165049856 msec\nrounds: 103"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[ethanol_100]",
            "value": 376.50643321109897,
            "unit": "iter/sec",
            "range": "stddev: 0.00007608152979998771",
            "extra": "mean: 2.6559971139704848 msec\nrounds: 272"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[ethanol_1000]",
            "value": 47.0966931122942,
            "unit": "iter/sec",
            "range": "stddev: 0.018852109332706597",
            "extra": "mean: 21.232913266663267 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[periodic_100]",
            "value": 374.1395857740824,
            "unit": "iter/sec",
            "range": "stddev: 0.00008401762429137365",
            "extra": "mean: 2.6727992386345143 msec\nrounds: 264"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[periodic_1000]",
            "value": 54.3047479081818,
            "unit": "iter/sec",
            "range": "stddev: 0.0003924441073413131",
            "extra": "mean: 18.414596117650614 msec\nrounds: 51"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[ethanol_100]",
            "value": 147.67091738527608,
            "unit": "iter/sec",
            "range": "stddev: 0.00038453940780531213",
            "extra": "mean: 6.771814096549437 msec\nrounds: 145"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[ethanol_1000]",
            "value": 13.75779671652044,
            "unit": "iter/sec",
            "range": "stddev: 0.00811786043049189",
            "extra": "mean: 72.6860572666548 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[periodic_100]",
            "value": 89.29128212624752,
            "unit": "iter/sec",
            "range": "stddev: 0.00030477164442175306",
            "extra": "mean: 11.199301613634754 msec\nrounds: 88"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[periodic_1000]",
            "value": 9.00416532688014,
            "unit": "iter/sec",
            "range": "stddev: 0.00040811435613642005",
            "extra": "mean: 111.05971111111204 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[ethanol_100]",
            "value": 2563.756803354136,
            "unit": "iter/sec",
            "range": "stddev: 0.000012581053072560154",
            "extra": "mean: 390.0525973024081 usec\nrounds: 2076"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[ethanol_1000]",
            "value": 2056.57527349179,
            "unit": "iter/sec",
            "range": "stddev: 0.000015622337632760458",
            "extra": "mean: 486.2452704209234 usec\nrounds: 1616"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[periodic_100]",
            "value": 2576.572478463492,
            "unit": "iter/sec",
            "range": "stddev: 0.000013375174229032731",
            "extra": "mean: 388.11250541507684 usec\nrounds: 2216"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[periodic_1000]",
            "value": 2024.736008557306,
            "unit": "iter/sec",
            "range": "stddev: 0.000033968936263641205",
            "extra": "mean: 493.89154723066065 usec\nrounds: 1535"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[ethanol_100]",
            "value": 63.20760473855655,
            "unit": "iter/sec",
            "range": "stddev: 0.0005548956308267583",
            "extra": "mean: 15.820881112901933 msec\nrounds: 62"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[ethanol_1000]",
            "value": 6.445208546015475,
            "unit": "iter/sec",
            "range": "stddev: 0.0003211717733929619",
            "extra": "mean: 155.15401757142757 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[periodic_100]",
            "value": 63.81015137891229,
            "unit": "iter/sec",
            "range": "stddev: 0.00010923274048712126",
            "extra": "mean: 15.671487661295155 msec\nrounds: 62"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[periodic_1000]",
            "value": 6.331627986821541,
            "unit": "iter/sec",
            "range": "stddev: 0.0031863073583266364",
            "extra": "mean: 157.93726385715803 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 236.62889073971647,
            "unit": "iter/sec",
            "range": "stddev: 0.00132285517536395",
            "extra": "mean: 4.22602665665185 msec\nrounds: 233"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 17.09486763673627,
            "unit": "iter/sec",
            "range": "stddev: 0.04106022177776643",
            "extra": "mean: 58.49708937500253 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[periodic_100]",
            "value": 237.3052415190572,
            "unit": "iter/sec",
            "range": "stddev: 0.00997014801725806",
            "extra": "mean: 4.213981931451326 msec\nrounds: 248"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 21.34564670825092,
            "unit": "iter/sec",
            "range": "stddev: 0.030165086908330804",
            "extra": "mean: 46.84795985185407 msec\nrounds: 27"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[ethanol_100]",
            "value": 23.613657725211937,
            "unit": "iter/sec",
            "range": "stddev: 0.0014595882907938716",
            "extra": "mean: 42.34837362499396 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 2.817484842100591,
            "unit": "iter/sec",
            "range": "stddev: 0.0027227703122341585",
            "extra": "mean: 354.926488000001 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[periodic_100]",
            "value": 11.209199635521857,
            "unit": "iter/sec",
            "range": "stddev: 0.001964713707253435",
            "extra": "mean: 89.21243554544328 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[periodic_1000]",
            "value": 1.134096317241064,
            "unit": "iter/sec",
            "range": "stddev: 0.06118598400234592",
            "extra": "mean: 881.7593222000028 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[ethanol_100]",
            "value": 204.67737294015308,
            "unit": "iter/sec",
            "range": "stddev: 0.0003378700421155684",
            "extra": "mean: 4.885737908568899 msec\nrounds: 175"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 20.873710898943227,
            "unit": "iter/sec",
            "range": "stddev: 0.03148635703955035",
            "extra": "mean: 47.90715004348494 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[periodic_100]",
            "value": 231.70183446474684,
            "unit": "iter/sec",
            "range": "stddev: 0.000720464083303323",
            "extra": "mean: 4.3158915953777175 msec\nrounds: 173"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[periodic_1000]",
            "value": 26.776416485880997,
            "unit": "iter/sec",
            "range": "stddev: 0.0031247094664013848",
            "extra": "mean: 37.346296900008724 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 220.29475592467395,
            "unit": "iter/sec",
            "range": "stddev: 0.0013848955354978415",
            "extra": "mean: 4.5393726954713935 msec\nrounds: 243"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 22.061561668413937,
            "unit": "iter/sec",
            "range": "stddev: 0.03267409976131593",
            "extra": "mean: 45.327706851855545 msec\nrounds: 27"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[periodic_100]",
            "value": 269.27809107770975,
            "unit": "iter/sec",
            "range": "stddev: 0.0006119548367647471",
            "extra": "mean: 3.713632980677268 msec\nrounds: 207"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 24.515068424770803,
            "unit": "iter/sec",
            "range": "stddev: 0.029877956913415278",
            "extra": "mean: 40.7912383793132 msec\nrounds: 29"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[ethanol_100]",
            "value": 129.29739318147946,
            "unit": "iter/sec",
            "range": "stddev: 0.001651066787975371",
            "extra": "mean: 7.734107976921223 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[ethanol_1000]",
            "value": 12.581425201536055,
            "unit": "iter/sec",
            "range": "stddev: 0.041630992085240306",
            "extra": "mean: 79.48225133333153 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[periodic_100]",
            "value": 129.82352142752808,
            "unit": "iter/sec",
            "range": "stddev: 0.012563976093777535",
            "extra": "mean: 7.702764406665969 msec\nrounds: 150"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[periodic_1000]",
            "value": 15.974006138766669,
            "unit": "iter/sec",
            "range": "stddev: 0.0019569885032109375",
            "extra": "mean: 62.6017037500155 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[ethanol_100]",
            "value": 51.74872309713862,
            "unit": "iter/sec",
            "range": "stddev: 0.01980754171729898",
            "extra": "mean: 19.324148310343407 msec\nrounds: 58"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[ethanol_1000]",
            "value": 5.801614051187433,
            "unit": "iter/sec",
            "range": "stddev: 0.0024739100803397407",
            "extra": "mean: 172.36582633333342 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[periodic_100]",
            "value": 44.73768590250114,
            "unit": "iter/sec",
            "range": "stddev: 0.0011498304300959436",
            "extra": "mean: 22.35251957777488 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[periodic_1000]",
            "value": 4.471430461310816,
            "unit": "iter/sec",
            "range": "stddev: 0.0057722731667452275",
            "extra": "mean: 223.64207799998894 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[ethanol_100]",
            "value": 2.1605331948759328,
            "unit": "iter/sec",
            "range": "stddev: 0.0018741105658907642",
            "extra": "mean: 462.8487090000135 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[ethanol_1000]",
            "value": 0.21660545004664816,
            "unit": "iter/sec",
            "range": "stddev: 0.023917998950153067",
            "extra": "mean: 4.616689006599972 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[periodic_100]",
            "value": 2.4592103953099076,
            "unit": "iter/sec",
            "range": "stddev: 0.0017771029976026802",
            "extra": "mean: 406.6345855999771 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[periodic_1000]",
            "value": 0.23860066488381157,
            "unit": "iter/sec",
            "range": "stddev: 0.07142850415411964",
            "extra": "mean: 4.191103157599992 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[ethanol_100]",
            "value": 18.311695591303156,
            "unit": "iter/sec",
            "range": "stddev: 0.0017700476913242935",
            "extra": "mean: 54.60990736843254 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[ethanol_1000]",
            "value": 1.82912916822629,
            "unit": "iter/sec",
            "range": "stddev: 0.0037444464861207394",
            "extra": "mean: 546.7082463999532 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[periodic_100]",
            "value": 17.286852092409916,
            "unit": "iter/sec",
            "range": "stddev: 0.005262604586037757",
            "extra": "mean: 57.84743194737386 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[periodic_1000]",
            "value": 1.8133022212450418,
            "unit": "iter/sec",
            "range": "stddev: 0.0032105934238910792",
            "extra": "mean: 551.4800502000071 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[ethanol_100]",
            "value": 214.07307989622902,
            "unit": "iter/sec",
            "range": "stddev: 0.0006091337894782669",
            "extra": "mean: 4.671301970732357 msec\nrounds: 205"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[ethanol_1000]",
            "value": 18.116485101574437,
            "unit": "iter/sec",
            "range": "stddev: 0.03528530056410135",
            "extra": "mean: 55.198345285703 msec\nrounds: 21"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[periodic_100]",
            "value": 226.6555618713013,
            "unit": "iter/sec",
            "range": "stddev: 0.0008131389595659355",
            "extra": "mean: 4.4119808565201515 msec\nrounds: 230"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[periodic_1000]",
            "value": 23.077181652301363,
            "unit": "iter/sec",
            "range": "stddev: 0.0028105572120889232",
            "extra": "mean: 43.33284779167457 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[ethanol_100]",
            "value": 1.4207347216067523,
            "unit": "iter/sec",
            "range": "stddev: 0.010676553585648466",
            "extra": "mean: 703.8611676000073 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[ethanol_1000]",
            "value": 0.14110624431993113,
            "unit": "iter/sec",
            "range": "stddev: 0.0501242367795818",
            "extra": "mean: 7.086858592400017 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[periodic_100]",
            "value": 1.4495609485145273,
            "unit": "iter/sec",
            "range": "stddev: 0.008671634126917682",
            "extra": "mean: 689.8640591999765 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[periodic_1000]",
            "value": 0.14913956437013218,
            "unit": "iter/sec",
            "range": "stddev: 0.061410404567645786",
            "extra": "mean: 6.705128878600021 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[ethanol_100]",
            "value": 11.58067566236097,
            "unit": "iter/sec",
            "range": "stddev: 0.000288206045771732",
            "extra": "mean: 86.35074750000626 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[ethanol_1000]",
            "value": 1.1227302812218551,
            "unit": "iter/sec",
            "range": "stddev: 0.02543468170407579",
            "extra": "mean: 890.6858724000131 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[periodic_100]",
            "value": 15.05070244517878,
            "unit": "iter/sec",
            "range": "stddev: 0.001620221980113156",
            "extra": "mean: 66.44208160000744 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[periodic_1000]",
            "value": 1.4872307082287977,
            "unit": "iter/sec",
            "range": "stddev: 0.005609137407877397",
            "extra": "mean: 672.39063479999 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[ethanol_100]",
            "value": 23.365072905931676,
            "unit": "iter/sec",
            "range": "stddev: 0.0015641053993347047",
            "extra": "mean: 42.79892487500566 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.12520866084944,
            "unit": "iter/sec",
            "range": "stddev: 0.07122041337630544",
            "extra": "mean: 470.5420312000342 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[periodic_100]",
            "value": 23.434900978733268,
            "unit": "iter/sec",
            "range": "stddev: 0.0019345390617650409",
            "extra": "mean: 42.671398565220365 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[periodic_1000]",
            "value": 2.3756566937525,
            "unit": "iter/sec",
            "range": "stddev: 0.0029567573664465428",
            "extra": "mean: 420.9362415999749 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[ethanol_100]",
            "value": 32.11407384494843,
            "unit": "iter/sec",
            "range": "stddev: 0.0029724479096370745",
            "extra": "mean: 31.1389954705887 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[ethanol_1000]",
            "value": 3.2875807514488415,
            "unit": "iter/sec",
            "range": "stddev: 0.0050339049766975836",
            "extra": "mean: 304.17503799999395 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[periodic_100]",
            "value": 30.695435782507435,
            "unit": "iter/sec",
            "range": "stddev: 0.0044674557911388215",
            "extra": "mean: 32.5781333448237 msec\nrounds: 29"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[periodic_1000]",
            "value": 3.366637598264735,
            "unit": "iter/sec",
            "range": "stddev: 0.004291580670320183",
            "extra": "mean: 297.03226760000234 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[ethanol_100]",
            "value": 59.62835791136045,
            "unit": "iter/sec",
            "range": "stddev: 0.0006498679590012839",
            "extra": "mean: 16.770543999996335 msec\nrounds: 57"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[ethanol_1000]",
            "value": 4.933515432128295,
            "unit": "iter/sec",
            "range": "stddev: 0.0742641938436792",
            "extra": "mean: 202.6952208333531 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[periodic_100]",
            "value": 44.57398021699704,
            "unit": "iter/sec",
            "range": "stddev: 0.0009593484005605516",
            "extra": "mean: 22.434613088886284 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[periodic_1000]",
            "value": 4.159022376606983,
            "unit": "iter/sec",
            "range": "stddev: 0.01751580620537617",
            "extra": "mean: 240.44112039998708 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[ethanol_100]",
            "value": 2.1749783507114624,
            "unit": "iter/sec",
            "range": "stddev: 0.002587854908019257",
            "extra": "mean: 459.77469139997993 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[ethanol_1000]",
            "value": 0.21744347129611144,
            "unit": "iter/sec",
            "range": "stddev: 0.027208973140111774",
            "extra": "mean: 4.598896412199997 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[periodic_100]",
            "value": 2.465926735528397,
            "unit": "iter/sec",
            "range": "stddev: 0.0005432028751907013",
            "extra": "mean: 405.52705220000007 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[periodic_1000]",
            "value": 0.24065611480856816,
            "unit": "iter/sec",
            "range": "stddev: 0.019806933337055063",
            "extra": "mean: 4.155306840200001 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[ethanol_100]",
            "value": 18.4705886551517,
            "unit": "iter/sec",
            "range": "stddev: 0.001697386406758877",
            "extra": "mean: 54.140126157868075 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[ethanol_1000]",
            "value": 1.7039735981014625,
            "unit": "iter/sec",
            "range": "stddev: 0.07867101374287232",
            "extra": "mean: 586.8635529999892 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[periodic_100]",
            "value": 18.439578922188762,
            "unit": "iter/sec",
            "range": "stddev: 0.00036104582678442055",
            "extra": "mean: 54.2311732941297 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[periodic_1000]",
            "value": 1.7947364469854552,
            "unit": "iter/sec",
            "range": "stddev: 0.022523503932895123",
            "extra": "mean: 557.1848734000241 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 205.8900476358121,
            "unit": "iter/sec",
            "range": "stddev: 0.010549704802138604",
            "extra": "mean: 4.856961331947654 msec\nrounds: 241"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 18.60862873554135,
            "unit": "iter/sec",
            "range": "stddev: 0.04005863262026848",
            "extra": "mean: 53.738511000010476 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[periodic_100]",
            "value": 285.160583982561,
            "unit": "iter/sec",
            "range": "stddev: 0.00043755334201442094",
            "extra": "mean: 3.5067960165951795 msec\nrounds: 241"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 23.556320525754526,
            "unit": "iter/sec",
            "range": "stddev: 0.029602582446978356",
            "extra": "mean: 42.451451571423604 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[ethanol_100]",
            "value": 20.832457241704347,
            "unit": "iter/sec",
            "range": "stddev: 0.03251251815568875",
            "extra": "mean: 48.002018600000156 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 2.8134198022379917,
            "unit": "iter/sec",
            "range": "stddev: 0.002469096697598631",
            "extra": "mean: 355.4393123999944 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[periodic_100]",
            "value": 10.784097648827094,
            "unit": "iter/sec",
            "range": "stddev: 0.009162425627815426",
            "extra": "mean: 92.72913066664994 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[periodic_1000]",
            "value": 1.1451567246159917,
            "unit": "iter/sec",
            "range": "stddev: 0.05686399513694408",
            "extra": "mean: 873.2429181999805 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[ethanol_100]",
            "value": 193.60859959412926,
            "unit": "iter/sec",
            "range": "stddev: 0.00047616511465148586",
            "extra": "mean: 5.165059827385491 msec\nrounds: 168"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 18.958829252855296,
            "unit": "iter/sec",
            "range": "stddev: 0.030412776599828634",
            "extra": "mean: 52.745873000011066 msec\nrounds: 21"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[periodic_100]",
            "value": 227.21691149903407,
            "unit": "iter/sec",
            "range": "stddev: 0.0004686432752183811",
            "extra": "mean: 4.401080858826176 msec\nrounds: 170"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[periodic_1000]",
            "value": 26.703375333895806,
            "unit": "iter/sec",
            "range": "stddev: 0.002447609238953998",
            "extra": "mean: 37.448449399977335 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 199.9778030019957,
            "unit": "iter/sec",
            "range": "stddev: 0.009804448023417567",
            "extra": "mean: 5.000554986545283 msec\nrounds: 223"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 21.21406624282754,
            "unit": "iter/sec",
            "range": "stddev: 0.03450360553104524",
            "extra": "mean: 47.13853480768211 msec\nrounds: 26"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[periodic_100]",
            "value": 220.9324515058967,
            "unit": "iter/sec",
            "range": "stddev: 0.011467750447269845",
            "extra": "mean: 4.526270329161264 msec\nrounds: 240"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 27.178453195648267,
            "unit": "iter/sec",
            "range": "stddev: 0.003958496439484623",
            "extra": "mean: 36.7938525714229 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[ethanol_100]",
            "value": 138.64016931797144,
            "unit": "iter/sec",
            "range": "stddev: 0.0011318186110603613",
            "extra": "mean: 7.212916753632192 msec\nrounds: 69"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[ethanol_1000]",
            "value": 15.154657308976299,
            "unit": "iter/sec",
            "range": "stddev: 0.0017659267057825213",
            "extra": "mean: 65.98631560000285 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[periodic_100]",
            "value": 151.0076872194958,
            "unit": "iter/sec",
            "range": "stddev: 0.00052799652272661",
            "extra": "mean: 6.622179429491291 msec\nrounds: 156"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[periodic_1000]",
            "value": 13.203956962704495,
            "unit": "iter/sec",
            "range": "stddev: 0.04291621178382107",
            "extra": "mean: 75.73487272221276 msec\nrounds: 18"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[ethanol_100]",
            "value": 61.19726577557777,
            "unit": "iter/sec",
            "range": "stddev: 0.0007613758991152606",
            "extra": "mean: 16.340599327871832 msec\nrounds: 61"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[ethanol_1000]",
            "value": 6.10626727873099,
            "unit": "iter/sec",
            "range": "stddev: 0.0016475693260452",
            "extra": "mean: 163.76616914283204 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[periodic_100]",
            "value": 46.17389527614328,
            "unit": "iter/sec",
            "range": "stddev: 0.0007236828519489012",
            "extra": "mean: 21.657258804341577 msec\nrounds: 46"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[periodic_1000]",
            "value": 4.625631477910385,
            "unit": "iter/sec",
            "range": "stddev: 0.004398585883483401",
            "extra": "mean: 216.1866990000135 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[ethanol_100]",
            "value": 54.82245661278272,
            "unit": "iter/sec",
            "range": "stddev: 0.0008339542505863119",
            "extra": "mean: 18.240700285707995 msec\nrounds: 56"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[ethanol_1000]",
            "value": 6.196336679438221,
            "unit": "iter/sec",
            "range": "stddev: 0.05727307631729389",
            "extra": "mean: 161.3856786249812 msec\nrounds: 8"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[periodic_100]",
            "value": 58.33803510800613,
            "unit": "iter/sec",
            "range": "stddev: 0.001479709065298521",
            "extra": "mean: 17.141475508193164 msec\nrounds: 61"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[periodic_1000]",
            "value": 7.8721307825005935,
            "unit": "iter/sec",
            "range": "stddev: 0.004066743394080404",
            "extra": "mean: 127.03040988889016 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[ethanol_100]",
            "value": 31.44279567769372,
            "unit": "iter/sec",
            "range": "stddev: 0.0015421980298263689",
            "extra": "mean: 31.803787750000367 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[ethanol_1000]",
            "value": 3.1410910141769746,
            "unit": "iter/sec",
            "range": "stddev: 0.0036218226130966956",
            "extra": "mean: 318.3607209999991 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[periodic_100]",
            "value": 30.032006242526673,
            "unit": "iter/sec",
            "range": "stddev: 0.0009659149137043378",
            "extra": "mean: 33.29780874192664 msec\nrounds: 31"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[periodic_1000]",
            "value": 2.651065378792273,
            "unit": "iter/sec",
            "range": "stddev: 0.07848152622679189",
            "extra": "mean: 377.2068422000075 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[ethanol_100]",
            "value": 32.04858915446238,
            "unit": "iter/sec",
            "range": "stddev: 0.0015583132631549173",
            "extra": "mean: 31.202621593742208 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[ethanol_1000]",
            "value": 3.280773711216106,
            "unit": "iter/sec",
            "range": "stddev: 0.0025100154873174117",
            "extra": "mean: 304.8061487999803 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[periodic_100]",
            "value": 32.00820402278573,
            "unit": "iter/sec",
            "range": "stddev: 0.0006753283529273718",
            "extra": "mean: 31.241990312487644 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[periodic_1000]",
            "value": 3.2335510379127728,
            "unit": "iter/sec",
            "range": "stddev: 0.0034647374707067607",
            "extra": "mean: 309.2575277999913 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[ethanol_100]",
            "value": 182.63167636868522,
            "unit": "iter/sec",
            "range": "stddev: 0.012183361126613983",
            "extra": "mean: 5.475501401965251 msec\nrounds: 204"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[ethanol_1000]",
            "value": 18.25945289365197,
            "unit": "iter/sec",
            "range": "stddev: 0.038474459844229925",
            "extra": "mean: 54.766153500012976 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[periodic_100]",
            "value": 244.02115145481307,
            "unit": "iter/sec",
            "range": "stddev: 0.00030870142202175536",
            "extra": "mean: 4.098005414851 msec\nrounds: 229"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[periodic_1000]",
            "value": 19.931560866582466,
            "unit": "iter/sec",
            "range": "stddev: 0.03660949474084324",
            "extra": "mean: 50.17168533331547 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[ethanol_100]",
            "value": 1.366449409682548,
            "unit": "iter/sec",
            "range": "stddev: 0.0487207303185076",
            "extra": "mean: 731.8236539999816 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[ethanol_1000]",
            "value": 0.13930729964034225,
            "unit": "iter/sec",
            "range": "stddev: 0.06293474551535701",
            "extra": "mean: 7.178374733999999 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[periodic_100]",
            "value": 1.516174890014272,
            "unit": "iter/sec",
            "range": "stddev: 0.007790260245649444",
            "extra": "mean: 659.554518799996 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[periodic_1000]",
            "value": 0.14947741799895753,
            "unit": "iter/sec",
            "range": "stddev: 0.053405853742227685",
            "extra": "mean: 6.689973732399994 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[ethanol_100]",
            "value": 11.449168985159389,
            "unit": "iter/sec",
            "range": "stddev: 0.0025816849566496765",
            "extra": "mean: 87.34258366665888 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[ethanol_1000]",
            "value": 1.1041362597845537,
            "unit": "iter/sec",
            "range": "stddev: 0.07580815094423417",
            "extra": "mean: 905.6853184000374 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[periodic_100]",
            "value": 15.114230086319122,
            "unit": "iter/sec",
            "range": "stddev: 0.0004545714524943104",
            "extra": "mean: 66.16281439999814 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[periodic_1000]",
            "value": 1.5007048228278803,
            "unit": "iter/sec",
            "range": "stddev: 0.00269818480968883",
            "extra": "mean: 666.3535592000244 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[ethanol_100]",
            "value": 23.594522747032617,
            "unit": "iter/sec",
            "range": "stddev: 0.0016052257967704765",
            "extra": "mean: 42.38271783334824 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.320831483404367,
            "unit": "iter/sec",
            "range": "stddev: 0.0033653059856032933",
            "extra": "mean: 430.88005619999876 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[periodic_100]",
            "value": 23.699537201418064,
            "unit": "iter/sec",
            "range": "stddev: 0.0015492716126064576",
            "extra": "mean: 42.194916782601354 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[periodic_1000]",
            "value": 2.295435478576053,
            "unit": "iter/sec",
            "range": "stddev: 0.031502124590581645",
            "extra": "mean: 435.64718300003733 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[ethanol_100]",
            "value": 33.0226552586815,
            "unit": "iter/sec",
            "range": "stddev: 0.001990888290069469",
            "extra": "mean: 30.28224084848854 msec\nrounds: 33"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[ethanol_1000]",
            "value": 2.8632467051991513,
            "unit": "iter/sec",
            "range": "stddev: 0.07960843997999818",
            "extra": "mean: 349.25387260000207 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[periodic_100]",
            "value": 33.98671765085945,
            "unit": "iter/sec",
            "range": "stddev: 0.0011870856571884194",
            "extra": "mean: 29.423259117660404 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[periodic_1000]",
            "value": 3.347631778356541,
            "unit": "iter/sec",
            "range": "stddev: 0.005144915749475144",
            "extra": "mean: 298.7186364000081 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[ethanol_100]",
            "value": 59.65474730397093,
            "unit": "iter/sec",
            "range": "stddev: 0.0006607701099168538",
            "extra": "mean: 16.763125236362114 msec\nrounds: 55"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[ethanol_1000]",
            "value": 5.963559674570813,
            "unit": "iter/sec",
            "range": "stddev: 0.0023081401900643807",
            "extra": "mean: 167.6850831667025 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[periodic_100]",
            "value": 44.61459587659977,
            "unit": "iter/sec",
            "range": "stddev: 0.0008928526972634393",
            "extra": "mean: 22.41418935556238 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[periodic_1000]",
            "value": 4.501942051816004,
            "unit": "iter/sec",
            "range": "stddev: 0.002348743411037921",
            "extra": "mean: 222.1263597999041 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[ethanol_100]",
            "value": 2.1968643115247177,
            "unit": "iter/sec",
            "range": "stddev: 0.0009885718766003521",
            "extra": "mean: 455.1942487999895 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[ethanol_1000]",
            "value": 0.21583959910444808,
            "unit": "iter/sec",
            "range": "stddev: 0.08867623294437808",
            "extra": "mean: 4.633070132399962 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[periodic_100]",
            "value": 2.4451768966401937,
            "unit": "iter/sec",
            "range": "stddev: 0.0042642515669114546",
            "extra": "mean: 408.9683660000446 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[periodic_1000]",
            "value": 0.24242233603850152,
            "unit": "iter/sec",
            "range": "stddev: 0.030905083733494768",
            "extra": "mean: 4.125032438599964 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[ethanol_100]",
            "value": 18.183618916919347,
            "unit": "iter/sec",
            "range": "stddev: 0.0018390062195419124",
            "extra": "mean: 54.994553315760925 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[ethanol_1000]",
            "value": 1.8439859731792214,
            "unit": "iter/sec",
            "range": "stddev: 0.0028418673549459594",
            "extra": "mean: 542.3034744000233 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[periodic_100]",
            "value": 17.634688177124087,
            "unit": "iter/sec",
            "range": "stddev: 0.0032556804887077617",
            "extra": "mean: 56.70641805264304 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[periodic_1000]",
            "value": 1.7161346636507964,
            "unit": "iter/sec",
            "range": "stddev: 0.07764174830892265",
            "extra": "mean: 582.7048548000676 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 1442.6325812509835,
            "unit": "iter/sec",
            "range": "stddev: 0.00025272910409540443",
            "extra": "mean: 693.1771907805152 usec\nrounds: 781"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 193.25195175039573,
            "unit": "iter/sec",
            "range": "stddev: 0.005644566868926651",
            "extra": "mean: 5.174591981826918 msec\nrounds: 165"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[periodic_100]",
            "value": 976.7830987081257,
            "unit": "iter/sec",
            "range": "stddev: 0.0018487687652290429",
            "extra": "mean: 1.0237687377295743 msec\nrounds: 591"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 104.03461837462687,
            "unit": "iter/sec",
            "range": "stddev: 0.00962989781924853",
            "extra": "mean: 9.61218501709707 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[ethanol_100]",
            "value": 647.0398569089801,
            "unit": "iter/sec",
            "range": "stddev: 0.00045238725679067293",
            "extra": "mean: 1.5454998472229684 msec\nrounds: 432"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 96.51928463870993,
            "unit": "iter/sec",
            "range": "stddev: 0.0006348229049130666",
            "extra": "mean: 10.360623825002335 msec\nrounds: 80"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[periodic_100]",
            "value": 683.9340626155962,
            "unit": "iter/sec",
            "range": "stddev: 0.0007983123933396386",
            "extra": "mean: 1.4621292528926844 msec\nrounds: 605"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[periodic_1000]",
            "value": 97.98157600690797,
            "unit": "iter/sec",
            "range": "stddev: 0.00039687786243658906",
            "extra": "mean: 10.206000360001326 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[ethanol_100]",
            "value": 4789.253882540394,
            "unit": "iter/sec",
            "range": "stddev: 0.000011111678509947779",
            "extra": "mean: 208.80079121417626 usec\nrounds: 3597"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 2271.9330109474954,
            "unit": "iter/sec",
            "range": "stddev: 0.000016261297381604187",
            "extra": "mean: 440.1538228378293 usec\nrounds: 1874"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[periodic_100]",
            "value": 4738.574128776043,
            "unit": "iter/sec",
            "range": "stddev: 0.000011010226346201538",
            "extra": "mean: 211.0339466733839 usec\nrounds: 3563"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[periodic_1000]",
            "value": 2280.8539236606503,
            "unit": "iter/sec",
            "range": "stddev: 0.000016003267507832077",
            "extra": "mean: 438.43228609531144 usec\nrounds: 1877"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 314.9339962923044,
            "unit": "iter/sec",
            "range": "stddev: 0.00007606946570558687",
            "extra": "mean: 3.17526850633126 msec\nrounds: 158"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 33.55580283123022,
            "unit": "iter/sec",
            "range": "stddev: 0.005618596784621585",
            "extra": "mean: 29.801104894718982 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[periodic_100]",
            "value": 287.4968189085387,
            "unit": "iter/sec",
            "range": "stddev: 0.0005395538854234916",
            "extra": "mean: 3.478299355785671 msec\nrounds: 104"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 37.14551669695582,
            "unit": "iter/sec",
            "range": "stddev: 0.002682653680136036",
            "extra": "mean: 26.92114927780646 msec\nrounds: 18"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[ethanol_100]",
            "value": 482.8947745484684,
            "unit": "iter/sec",
            "range": "stddev: 0.00007265421204857653",
            "extra": "mean: 2.0708445249486327 msec\nrounds: 461"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[ethanol_1000]",
            "value": 72.97791739527398,
            "unit": "iter/sec",
            "range": "stddev: 0.0003270290316946826",
            "extra": "mean: 13.702775246156307 msec\nrounds: 65"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[periodic_100]",
            "value": 486.54037884686323,
            "unit": "iter/sec",
            "range": "stddev: 0.00005707132797725566",
            "extra": "mean: 2.0553278689223577 msec\nrounds: 473"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[periodic_1000]",
            "value": 72.65126615258866,
            "unit": "iter/sec",
            "range": "stddev: 0.0005139400169831839",
            "extra": "mean: 13.76438502667952 msec\nrounds: 75"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[ethanol_100]",
            "value": 13.066526875734061,
            "unit": "iter/sec",
            "range": "stddev: 0.004956341376401017",
            "extra": "mean: 76.53143100000867 msec\nrounds: 13"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[ethanol_1000]",
            "value": 1.3132097101857139,
            "unit": "iter/sec",
            "range": "stddev: 0.011418430528840631",
            "extra": "mean: 761.4929986000334 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[periodic_100]",
            "value": 10.48917795323563,
            "unit": "iter/sec",
            "range": "stddev: 0.0037906397954223224",
            "extra": "mean: 95.33635566660654 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[periodic_1000]",
            "value": 0.9682276949436073,
            "unit": "iter/sec",
            "range": "stddev: 0.03546660174418443",
            "extra": "mean: 1.0328149104000204 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[ethanol_100]",
            "value": 4.64904197559451,
            "unit": "iter/sec",
            "range": "stddev: 0.0012256849753231596",
            "extra": "mean: 215.09807939992243 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[ethanol_1000]",
            "value": 0.3858397442917971,
            "unit": "iter/sec",
            "range": "stddev: 0.11430191605479612",
            "extra": "mean: 2.5917495924000375 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[periodic_100]",
            "value": 4.351550954029693,
            "unit": "iter/sec",
            "range": "stddev: 0.003768379328819656",
            "extra": "mean: 229.80312320000849 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[periodic_1000]",
            "value": 0.39941963199509595,
            "unit": "iter/sec",
            "range": "stddev: 0.017262027524955096",
            "extra": "mean: 2.50363257060003 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 200.0487323360277,
            "unit": "iter/sec",
            "range": "stddev: 0.001173780812560753",
            "extra": "mean: 4.998781988382064 msec\nrounds: 172"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 21.506705054267357,
            "unit": "iter/sec",
            "range": "stddev: 0.02876985505707651",
            "extra": "mean: 46.497127173908034 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[periodic_100]",
            "value": 211.2754054162698,
            "unit": "iter/sec",
            "range": "stddev: 0.0003436001888467484",
            "extra": "mean: 4.733158589991717 msec\nrounds: 200"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 20.453461345009536,
            "unit": "iter/sec",
            "range": "stddev: 0.02882620583965477",
            "extra": "mean: 48.8914801818613 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[ethanol_100]",
            "value": 10.468209403673663,
            "unit": "iter/sec",
            "range": "stddev: 0.0009815658899101907",
            "extra": "mean: 95.52732100000453 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 1.8751852507230222,
            "unit": "iter/sec",
            "range": "stddev: 0.004439912527039374",
            "extra": "mean: 533.280644999968 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[periodic_100]",
            "value": 6.376511136694796,
            "unit": "iter/sec",
            "range": "stddev: 0.0015370517879186169",
            "extra": "mean: 156.8255709999968 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[periodic_1000]",
            "value": 0.783222320359803,
            "unit": "iter/sec",
            "range": "stddev: 0.08350318842421647",
            "extra": "mean: 1.2767766877999747 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[ethanol_100]",
            "value": 25.714547284930987,
            "unit": "iter/sec",
            "range": "stddev: 0.0002482867420509919",
            "extra": "mean: 38.88849330767768 msec\nrounds: 26"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 3.061005810916821,
            "unit": "iter/sec",
            "range": "stddev: 0.0006520052543905638",
            "extra": "mean: 326.6900037999221 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[periodic_100]",
            "value": 42.197095416985455,
            "unit": "iter/sec",
            "range": "stddev: 0.0006301160975802461",
            "extra": "mean: 23.698313595240336 msec\nrounds: 42"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[periodic_1000]",
            "value": 5.355369101518624,
            "unit": "iter/sec",
            "range": "stddev: 0.0011181505888376545",
            "extra": "mean: 186.72849266662675 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 58.23661773322648,
            "unit": "iter/sec",
            "range": "stddev: 0.0002405117480602661",
            "extra": "mean: 17.171326888880383 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 11.566770491878318,
            "unit": "iter/sec",
            "range": "stddev: 0.04700959193814584",
            "extra": "mean: 86.45455537499913 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[periodic_100]",
            "value": 55.566733056519105,
            "unit": "iter/sec",
            "range": "stddev: 0.0014084156232793933",
            "extra": "mean: 17.99637921817107 msec\nrounds: 55"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 13.69752469514501,
            "unit": "iter/sec",
            "range": "stddev: 0.033767003733081905",
            "extra": "mean: 73.00589137499003 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[ethanol_100]",
            "value": 133.06425727795965,
            "unit": "iter/sec",
            "range": "stddev: 0.001787034956286977",
            "extra": "mean: 7.515166134442002 msec\nrounds: 119"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[ethanol_1000]",
            "value": 15.258753247748734,
            "unit": "iter/sec",
            "range": "stddev: 0.03305528213298559",
            "extra": "mean: 65.53615382354646 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[periodic_100]",
            "value": 147.72903148170747,
            "unit": "iter/sec",
            "range": "stddev: 0.0003299054972011422",
            "extra": "mean: 6.769150179691152 msec\nrounds: 128"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[periodic_1000]",
            "value": 17.46102410029,
            "unit": "iter/sec",
            "range": "stddev: 0.0020830016289157933",
            "extra": "mean: 57.27040947062158 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[ethanol_100]",
            "value": 8.696265693354192,
            "unit": "iter/sec",
            "range": "stddev: 0.0029361564992921732",
            "extra": "mean: 114.99188677781704 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[ethanol_1000]",
            "value": 0.8210019307205793,
            "unit": "iter/sec",
            "range": "stddev: 0.043285147374066094",
            "extra": "mean: 1.2180239321999125 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[periodic_100]",
            "value": 6.474920214012236,
            "unit": "iter/sec",
            "range": "stddev: 0.004728845730886626",
            "extra": "mean: 154.44205749993975 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[periodic_1000]",
            "value": 0.6156900617627917,
            "unit": "iter/sec",
            "range": "stddev: 0.04537165005561612",
            "extra": "mean: 1.6241938308000043 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[ethanol_100]",
            "value": 55.652597883698505,
            "unit": "iter/sec",
            "range": "stddev: 0.00016599570271784962",
            "extra": "mean: 17.968613111103576 msec\nrounds: 54"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[ethanol_1000]",
            "value": 18.568733187172604,
            "unit": "iter/sec",
            "range": "stddev: 0.004103836971349362",
            "extra": "mean: 53.85397000000012 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[periodic_100]",
            "value": 54.53914893841678,
            "unit": "iter/sec",
            "range": "stddev: 0.00010386823321718042",
            "extra": "mean: 18.335452962956136 msec\nrounds: 54"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[periodic_1000]",
            "value": 13.361121105866603,
            "unit": "iter/sec",
            "range": "stddev: 0.00038369276999566975",
            "extra": "mean: 74.84401885713916 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[ethanol_100]",
            "value": 50.207067071633865,
            "unit": "iter/sec",
            "range": "stddev: 0.0001296117997847253",
            "extra": "mean: 19.917514770843542 msec\nrounds: 48"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[ethanol_1000]",
            "value": 4.81341702952884,
            "unit": "iter/sec",
            "range": "stddev: 0.01330976167973887",
            "extra": "mean: 207.7526202000172 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[periodic_100]",
            "value": 33.202708999482226,
            "unit": "iter/sec",
            "range": "stddev: 0.0008667598869256658",
            "extra": "mean: 30.118024406249333 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[periodic_1000]",
            "value": 3.344490148901517,
            "unit": "iter/sec",
            "range": "stddev: 0.0005242448927447816",
            "extra": "mean: 298.99923620000664 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[ethanol_100]",
            "value": 3.9425596561396077,
            "unit": "iter/sec",
            "range": "stddev: 0.006589302446895829",
            "extra": "mean: 253.64232560000343 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[ethanol_1000]",
            "value": 0.380748396993087,
            "unit": "iter/sec",
            "range": "stddev: 0.03278325664235158",
            "extra": "mean: 2.626406330000009 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[periodic_100]",
            "value": 3.8601540667157797,
            "unit": "iter/sec",
            "range": "stddev: 0.008140259229182645",
            "extra": "mean: 259.0570176000256 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[periodic_1000]",
            "value": 0.38428251434226635,
            "unit": "iter/sec",
            "range": "stddev: 0.03914630728011086",
            "extra": "mean: 2.602252152200026 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[ethanol_100]",
            "value": 135.49657337135878,
            "unit": "iter/sec",
            "range": "stddev: 0.0024574957207196594",
            "extra": "mean: 7.380260438463456 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[ethanol_1000]",
            "value": 134.9583137961108,
            "unit": "iter/sec",
            "range": "stddev: 0.0009975193832806478",
            "extra": "mean: 7.409695422771486 msec\nrounds: 123"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[periodic_100]",
            "value": 123.52739571597475,
            "unit": "iter/sec",
            "range": "stddev: 0.001720549960412836",
            "extra": "mean: 8.095370214873546 msec\nrounds: 121"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[periodic_1000]",
            "value": 126.53070520624604,
            "unit": "iter/sec",
            "range": "stddev: 0.00139298177603654",
            "extra": "mean: 7.9032199999991475 msec\nrounds: 122"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[ethanol_100]",
            "value": 1.9317735431850218,
            "unit": "iter/sec",
            "range": "stddev: 0.003319588131632943",
            "extra": "mean: 517.6590204001059 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[ethanol_1000]",
            "value": 1.9344926252149581,
            "unit": "iter/sec",
            "range": "stddev: 0.003462834276764133",
            "extra": "mean: 516.9314097999631 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[periodic_100]",
            "value": 2.1587020610092864,
            "unit": "iter/sec",
            "range": "stddev: 0.025502566750143858",
            "extra": "mean: 463.24132360000476 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[periodic_1000]",
            "value": 2.2021322063168527,
            "unit": "iter/sec",
            "range": "stddev: 0.00455625161050114",
            "extra": "mean: 454.1053425999962 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[ethanol_100]",
            "value": 19.00584148339471,
            "unit": "iter/sec",
            "range": "stddev: 0.0002128856416753402",
            "extra": "mean: 52.615402526307186 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[ethanol_1000]",
            "value": 19.02079256035546,
            "unit": "iter/sec",
            "range": "stddev: 0.00013283596597698632",
            "extra": "mean: 52.5740447895044 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[periodic_100]",
            "value": 21.83834878608539,
            "unit": "iter/sec",
            "range": "stddev: 0.000215639415145271",
            "extra": "mean: 45.79100781819017 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[periodic_1000]",
            "value": 22.01630401981036,
            "unit": "iter/sec",
            "range": "stddev: 0.00015612508103800371",
            "extra": "mean: 45.4208844091268 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[ethanol_100]",
            "value": 36.49022653251685,
            "unit": "iter/sec",
            "range": "stddev: 0.0018128307847537256",
            "extra": "mean: 27.404598300010246 msec\nrounds: 30"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[ethanol_1000]",
            "value": 36.182784500093135,
            "unit": "iter/sec",
            "range": "stddev: 0.0008352958631507626",
            "extra": "mean: 27.637452833333654 msec\nrounds: 36"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[periodic_100]",
            "value": 33.13068157426547,
            "unit": "iter/sec",
            "range": "stddev: 0.003530174505773303",
            "extra": "mean: 30.183502194435935 msec\nrounds: 36"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[periodic_1000]",
            "value": 35.80091152480219,
            "unit": "iter/sec",
            "range": "stddev: 0.001931188479827769",
            "extra": "mean: 27.932249694458733 msec\nrounds: 36"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[ethanol_100]",
            "value": 166.85888929072127,
            "unit": "iter/sec",
            "range": "stddev: 0.00035148759153518156",
            "extra": "mean: 5.993087957439785 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[ethanol_1000]",
            "value": 169.59970911272129,
            "unit": "iter/sec",
            "range": "stddev: 0.0004126108435090447",
            "extra": "mean: 5.8962365279492825 msec\nrounds: 161"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[periodic_100]",
            "value": 174.8670383532761,
            "unit": "iter/sec",
            "range": "stddev: 0.00017820472172714113",
            "extra": "mean: 5.718630620252998 msec\nrounds: 158"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[periodic_1000]",
            "value": 172.24349468326312,
            "unit": "iter/sec",
            "range": "stddev: 0.00022894523514886719",
            "extra": "mean: 5.805734503000477 msec\nrounds: 167"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[ethanol_100]",
            "value": 72.97499468418306,
            "unit": "iter/sec",
            "range": "stddev: 0.0023965934579673626",
            "extra": "mean: 13.703324054050869 msec\nrounds: 74"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[ethanol_1000]",
            "value": 71.41906837596596,
            "unit": "iter/sec",
            "range": "stddev: 0.0018865257423647534",
            "extra": "mean: 14.00186284614882 msec\nrounds: 78"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[periodic_100]",
            "value": 64.92008369624548,
            "unit": "iter/sec",
            "range": "stddev: 0.003099050248640106",
            "extra": "mean: 15.403553770492643 msec\nrounds: 61"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[periodic_1000]",
            "value": 62.968623994001234,
            "unit": "iter/sec",
            "range": "stddev: 0.0019357111103518445",
            "extra": "mean: 15.880925079373911 msec\nrounds: 63"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[ethanol_100]",
            "value": 10.322396868960173,
            "unit": "iter/sec",
            "range": "stddev: 0.007575604683517945",
            "extra": "mean: 96.87672472728082 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[ethanol_1000]",
            "value": 11.027634457958257,
            "unit": "iter/sec",
            "range": "stddev: 0.0006192949622431032",
            "extra": "mean: 90.68127927275782 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[periodic_100]",
            "value": 13.071922886850409,
            "unit": "iter/sec",
            "range": "stddev: 0.0018092062202882482",
            "extra": "mean: 76.49983928576732 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[periodic_1000]",
            "value": 13.18961378699511,
            "unit": "iter/sec",
            "range": "stddev: 0.0003444250531075169",
            "extra": "mean: 75.81723135714518 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[ethanol_100]",
            "value": 381.387329347853,
            "unit": "iter/sec",
            "range": "stddev: 0.00003542016283551747",
            "extra": "mean: 2.6220063516791017 msec\nrounds: 327"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[ethanol_1000]",
            "value": 381.8310804781432,
            "unit": "iter/sec",
            "range": "stddev: 0.0000462559061337751",
            "extra": "mean: 2.6189591448337906 msec\nrounds: 359"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[periodic_100]",
            "value": 276.148569087825,
            "unit": "iter/sec",
            "range": "stddev: 0.00004341303081729469",
            "extra": "mean: 3.6212391152458387 msec\nrounds: 269"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[periodic_1000]",
            "value": 275.76593730948554,
            "unit": "iter/sec",
            "range": "stddev: 0.00019301829447618445",
            "extra": "mean: 3.626263670402932 msec\nrounds: 267"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[ethanol_100]",
            "value": 27.26285891642894,
            "unit": "iter/sec",
            "range": "stddev: 0.004096843740442419",
            "extra": "mean: 36.67993892589846 msec\nrounds: 27"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[ethanol_1000]",
            "value": 26.9154277655476,
            "unit": "iter/sec",
            "range": "stddev: 0.004122787996442664",
            "extra": "mean: 37.153412857143 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[periodic_100]",
            "value": 25.179361113480603,
            "unit": "iter/sec",
            "range": "stddev: 0.005871104113108139",
            "extra": "mean: 39.71506645832316 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[periodic_1000]",
            "value": 25.506519155990766,
            "unit": "iter/sec",
            "range": "stddev: 0.007194650319162895",
            "extra": "mean: 39.20566322218561 msec\nrounds: 27"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_encode_current",
            "value": 44091.25308549572,
            "unit": "iter/sec",
            "range": "stddev: 0.000004542553179420889",
            "extra": "mean: 22.680235421318987 usec\nrounds: 10683"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_atoms_to_dict_new",
            "value": 239103.3172511249,
            "unit": "iter/sec",
            "range": "stddev: 0.0000010364114015715513",
            "extra": "mean: 4.182292456234399 usec\nrounds: 32251"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_decode_current",
            "value": 47260.85614838865,
            "unit": "iter/sec",
            "range": "stddev: 0.000023481270975671475",
            "extra": "mean: 21.159159640701827 usec\nrounds: 15347"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_dict_to_atoms_new",
            "value": 163788.476020448,
            "unit": "iter/sec",
            "range": "stddev: 0.00001477768799113461",
            "extra": "mean: 6.105435646615065 usec\nrounds: 52701"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_read_current_aseio",
            "value": 27.645517933899708,
            "unit": "iter/sec",
            "range": "stddev: 0.030041241065693745",
            "extra": "mean: 36.17222880001724 msec\nrounds: 35"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_read_new_aseio",
            "value": 23.0490014435718,
            "unit": "iter/sec",
            "range": "stddev: 0.04536074553666108",
            "extra": "mean: 43.38582747058193 msec\nrounds: 34"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_write_current_aseio",
            "value": 31.079475819186033,
            "unit": "iter/sec",
            "range": "stddev: 0.0007891905531136549",
            "extra": "mean: 32.17557483330135 msec\nrounds: 30"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_write_new_aseio",
            "value": 31.64456258142975,
            "unit": "iter/sec",
            "range": "stddev: 0.0007156842004907148",
            "extra": "mean: 31.6010056206888 msec\nrounds: 29"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_random_access_current",
            "value": 23.234002523308014,
            "unit": "iter/sec",
            "range": "stddev: 0.04594048200159253",
            "extra": "mean: 43.04036719445195 msec\nrounds: 36"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_random_access_new",
            "value": 22.313572138374568,
            "unit": "iter/sec",
            "range": "stddev: 0.04794635620217452",
            "extra": "mean: 44.815773727247105 msec\nrounds: 33"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_via_view",
            "value": 115.07850159120424,
            "unit": "iter/sec",
            "range": "stddev: 0.017863396902569766",
            "extra": "mean: 8.689720374986466 msec\nrounds: 112"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_manual_loop",
            "value": 36.848733147785865,
            "unit": "iter/sec",
            "range": "stddev: 0.0007017862457036106",
            "extra": "mean: 27.137975028595715 msec\nrounds: 35"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_selective_keys",
            "value": 889.5881203189704,
            "unit": "iter/sec",
            "range": "stddev: 0.00002958750283195197",
            "extra": "mean: 1.1241157308187077 msec\nrounds: 691"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_row_view_iteration",
            "value": 24.308010853926152,
            "unit": "iter/sec",
            "range": "stddev: 0.04537905676924922",
            "extra": "mean: 41.138701393926816 msec\nrounds: 33"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_direct_iteration",
            "value": 23.233122121794636,
            "unit": "iter/sec",
            "range": "stddev: 0.04410318119450968",
            "extra": "mean: 43.04199817647045 msec\nrounds: 34"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_multi_column_view",
            "value": 84.41989643632836,
            "unit": "iter/sec",
            "range": "stddev: 0.0025279305707959516",
            "extra": "mean: 11.845548765322468 msec\nrounds: 98"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_multi_column_manual",
            "value": 36.23628005141413,
            "unit": "iter/sec",
            "range": "stddev: 0.0011708345876113792",
            "extra": "mean: 27.596651714280338 msec\nrounds: 35"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[ethanol_100]",
            "value": 196.4200075779007,
            "unit": "iter/sec",
            "range": "stddev: 0.001027745111839111",
            "extra": "mean: 5.091131052947329 msec\nrounds: 170"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[ethanol_1000]",
            "value": 18.767897393347578,
            "unit": "iter/sec",
            "range": "stddev: 0.04043884415635429",
            "extra": "mean: 53.28247373914446 msec\nrounds: 23"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[periodic_100]",
            "value": 206.01145285047528,
            "unit": "iter/sec",
            "range": "stddev: 0.0002794426217497769",
            "extra": "mean: 4.854099061792491 msec\nrounds: 178"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[periodic_1000]",
            "value": 20.780909003592864,
            "unit": "iter/sec",
            "range": "stddev: 0.030555397454192307",
            "extra": "mean: 48.12109036361727 msec\nrounds: 22"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[ethanol_100]",
            "value": 10.128776406893843,
            "unit": "iter/sec",
            "range": "stddev: 0.0030533291469787625",
            "extra": "mean: 98.72860845455928 msec\nrounds: 11"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[ethanol_1000]",
            "value": 1.724357868718219,
            "unit": "iter/sec",
            "range": "stddev: 0.032201895160047574",
            "extra": "mean: 579.9260224000591 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[periodic_100]",
            "value": 6.133276567700531,
            "unit": "iter/sec",
            "range": "stddev: 0.004939289931771533",
            "extra": "mean: 163.04498728563235 msec\nrounds: 7"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[periodic_1000]",
            "value": 0.7701229068565827,
            "unit": "iter/sec",
            "range": "stddev: 0.0738727831759638",
            "extra": "mean: 1.2984940339999866 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[ethanol_100]",
            "value": 25.444126718064616,
            "unit": "iter/sec",
            "range": "stddev: 0.00047327932601281533",
            "extra": "mean: 39.30180080772935 msec\nrounds: 26"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[ethanol_1000]",
            "value": 3.0477461273701025,
            "unit": "iter/sec",
            "range": "stddev: 0.0008499364588552018",
            "extra": "mean: 328.11131840003327 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[periodic_100]",
            "value": 42.2824618980379,
            "unit": "iter/sec",
            "range": "stddev: 0.00021070129178599748",
            "extra": "mean: 23.650467714284268 msec\nrounds: 42"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[periodic_1000]",
            "value": 5.351652577649637,
            "unit": "iter/sec",
            "range": "stddev: 0.000980252730228193",
            "extra": "mean: 186.85816866669333 msec\nrounds: 6"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[ethanol_100]",
            "value": 8.55658976604643,
            "unit": "iter/sec",
            "range": "stddev: 0.0031075937221354253",
            "extra": "mean: 116.86898955564276 msec\nrounds: 9"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[ethanol_1000]",
            "value": 0.8524248263546539,
            "unit": "iter/sec",
            "range": "stddev: 0.07924614993773411",
            "extra": "mean: 1.173123974200098 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[periodic_100]",
            "value": 6.186885263349064,
            "unit": "iter/sec",
            "range": "stddev: 0.005846178471499137",
            "extra": "mean: 161.63221999993635 msec\nrounds: 7"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[periodic_1000]",
            "value": 0.6101131068079065,
            "unit": "iter/sec",
            "range": "stddev: 0.051980377233071404",
            "extra": "mean: 1.6390403498000068 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[ethanol_100]",
            "value": 54.997300556121544,
            "unit": "iter/sec",
            "range": "stddev: 0.00026002144892426385",
            "extra": "mean: 18.1827106037606 msec\nrounds: 53"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[ethanol_1000]",
            "value": 18.659762188024864,
            "unit": "iter/sec",
            "range": "stddev: 0.0014134415230143815",
            "extra": "mean: 53.59125105258643 msec\nrounds: 19"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[periodic_100]",
            "value": 49.600419213587976,
            "unit": "iter/sec",
            "range": "stddev: 0.003293603648562075",
            "extra": "mean: 20.161119923076196 msec\nrounds: 52"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[periodic_1000]",
            "value": 12.876521957596907,
            "unit": "iter/sec",
            "range": "stddev: 0.0032580144062954322",
            "extra": "mean: 77.66072261539684 msec\nrounds: 13"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[ethanol_100]",
            "value": 50.0203682938925,
            "unit": "iter/sec",
            "range": "stddev: 0.00023058840768460902",
            "extra": "mean: 19.991856000030698 msec\nrounds: 49"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[ethanol_1000]",
            "value": 5.032175507941324,
            "unit": "iter/sec",
            "range": "stddev: 0.0013023463007003368",
            "extra": "mean: 198.72120883341418 msec\nrounds: 6"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[periodic_100]",
            "value": 33.33114687742222,
            "unit": "iter/sec",
            "range": "stddev: 0.00020559312202426432",
            "extra": "mean: 30.001967939404384 msec\nrounds: 33"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[periodic_1000]",
            "value": 3.321624105688344,
            "unit": "iter/sec",
            "range": "stddev: 0.0016161645812388565",
            "extra": "mean: 301.05754539999907 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[ethanol_100]",
            "value": 3.552913693571615,
            "unit": "iter/sec",
            "range": "stddev: 0.021419127818207956",
            "extra": "mean: 281.45913079997626 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[ethanol_1000]",
            "value": 0.3659841044210066,
            "unit": "iter/sec",
            "range": "stddev: 0.07972114572306047",
            "extra": "mean: 2.732359104999978 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[periodic_100]",
            "value": 3.811530004348299,
            "unit": "iter/sec",
            "range": "stddev: 0.010597913252379836",
            "extra": "mean: 262.36183340001844 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[periodic_1000]",
            "value": 0.36333572654970747,
            "unit": "iter/sec",
            "range": "stddev: 0.052917992303139476",
            "extra": "mean: 2.7522754491999875 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "name": "Fabian Zills",
            "username": "PythonFZ",
            "email": "46721498+PythonFZ@users.noreply.github.com"
          },
          "committer": {
            "name": "GitHub",
            "username": "web-flow",
            "email": "noreply@github.com"
          },
          "id": "cd81592cf0e195a2bcba16b5dec612a1e0f5cf6d",
          "message": "build: switch to hatchling + hatch-vcs and add PyPI publish workflow (#15)\n\nReplace uv_build with hatchling/hatch-vcs for automatic git-tag versioning.\nAdd GitHub Actions workflow for publishing to PyPI on release via trusted publishing.\n\nCo-authored-by: Claude Opus 4.6 <noreply@anthropic.com>",
          "timestamp": "2026-03-10T14:29:08Z",
          "url": "https://github.com/zincware/asebytes/commit/cd81592cf0e195a2bcba16b5dec612a1e0f5cf6d"
        },
        "date": 1773154449746,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 3463.842621854439,
            "unit": "iter/sec",
            "range": "stddev: 0.000009861900271783782",
            "extra": "mean: 288.6967189821775 usec\nrounds: 1886"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 322.7334917429796,
            "unit": "iter/sec",
            "range": "stddev: 0.0005793649284751216",
            "extra": "mean: 3.098531840000002 msec\nrounds: 300"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[periodic_100]",
            "value": 3337.0260138676663,
            "unit": "iter/sec",
            "range": "stddev: 0.0000214644821283913",
            "extra": "mean: 299.66802651351946 usec\nrounds: 2527"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 328.3032872735194,
            "unit": "iter/sec",
            "range": "stddev: 0.00003283568677762985",
            "extra": "mean: 3.0459640179200207 msec\nrounds: 279"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[ethanol_100]",
            "value": 127.2615721434357,
            "unit": "iter/sec",
            "range": "stddev: 0.00037523216402912213",
            "extra": "mean: 7.857831575999284 msec\nrounds: 125"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 14.266080287017592,
            "unit": "iter/sec",
            "range": "stddev: 0.0011153897004610356",
            "extra": "mean: 70.09633899999983 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[periodic_100]",
            "value": 48.08868536553028,
            "unit": "iter/sec",
            "range": "stddev: 0.0009043329126885135",
            "extra": "mean: 20.794912408164826 msec\nrounds: 49"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[periodic_1000]",
            "value": 5.02658407003817,
            "unit": "iter/sec",
            "range": "stddev: 0.0010713257422784264",
            "extra": "mean: 198.9422610000048 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[ethanol_100]",
            "value": 1882.7492699489528,
            "unit": "iter/sec",
            "range": "stddev: 0.000013618327200325303",
            "extra": "mean: 531.1381690388934 usec\nrounds: 1124"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 209.93283484965406,
            "unit": "iter/sec",
            "range": "stddev: 0.0005620353161647363",
            "extra": "mean: 4.763428268456252 msec\nrounds: 149"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[periodic_100]",
            "value": 1773.8672034842,
            "unit": "iter/sec",
            "range": "stddev: 0.00001915978834655799",
            "extra": "mean: 563.7400579005107 usec\nrounds: 829"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[periodic_1000]",
            "value": 204.54961407091508,
            "unit": "iter/sec",
            "range": "stddev: 0.00008426429854242999",
            "extra": "mean: 4.88878947311683 msec\nrounds: 93"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 904.6360795120682,
            "unit": "iter/sec",
            "range": "stddev: 0.000035091670771264094",
            "extra": "mean: 1.105416888235729 msec\nrounds: 170"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 248.32563241271365,
            "unit": "iter/sec",
            "range": "stddev: 0.00010906755232751714",
            "extra": "mean: 4.026970515625283 msec\nrounds: 64"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[periodic_100]",
            "value": 925.5206014384006,
            "unit": "iter/sec",
            "range": "stddev: 0.00004116777100594689",
            "extra": "mean: 1.0804729775283737 msec\nrounds: 178"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 246.72356344796725,
            "unit": "iter/sec",
            "range": "stddev: 0.00012365999786043456",
            "extra": "mean: 4.053119150943582 msec\nrounds: 106"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[ethanol_100]",
            "value": 346.22014357141325,
            "unit": "iter/sec",
            "range": "stddev: 0.00006939595820956399",
            "extra": "mean: 2.8883356978729187 msec\nrounds: 235"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[ethanol_1000]",
            "value": 49.09346703906028,
            "unit": "iter/sec",
            "range": "stddev: 0.0004960525294640045",
            "extra": "mean: 20.369309000001348 msec\nrounds: 43"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[periodic_100]",
            "value": 333.1926733241512,
            "unit": "iter/sec",
            "range": "stddev: 0.00011177841312632452",
            "extra": "mean: 3.001266474509588 msec\nrounds: 255"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[periodic_1000]",
            "value": 48.20759186633809,
            "unit": "iter/sec",
            "range": "stddev: 0.0009194826801664184",
            "extra": "mean: 20.743620688887177 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[ethanol_100]",
            "value": 142.37588509565185,
            "unit": "iter/sec",
            "range": "stddev: 0.00006711672055067778",
            "extra": "mean: 7.023661340740209 msec\nrounds: 135"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[ethanol_1000]",
            "value": 14.182378504385229,
            "unit": "iter/sec",
            "range": "stddev: 0.00041342652183821657",
            "extra": "mean: 70.51003466666734 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[periodic_100]",
            "value": 81.06665716308052,
            "unit": "iter/sec",
            "range": "stddev: 0.0017102444729819482",
            "extra": "mean: 12.33552776190482 msec\nrounds: 84"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[periodic_1000]",
            "value": 8.679447536346172,
            "unit": "iter/sec",
            "range": "stddev: 0.00032111977625651813",
            "extra": "mean: 115.21470644443512 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[ethanol_100]",
            "value": 1640.7453594076323,
            "unit": "iter/sec",
            "range": "stddev: 0.000025714964758550336",
            "extra": "mean: 609.479096964221 usec\nrounds: 1186"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[ethanol_1000]",
            "value": 230.59772933652437,
            "unit": "iter/sec",
            "range": "stddev: 0.015094931870762883",
            "extra": "mean: 4.336556144230905 msec\nrounds: 208"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[periodic_100]",
            "value": 596.662388369847,
            "unit": "iter/sec",
            "range": "stddev: 0.008997787496367527",
            "extra": "mean: 1.6759896710300772 msec\nrounds: 611"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[periodic_1000]",
            "value": 100.98917406660334,
            "unit": "iter/sec",
            "range": "stddev: 0.01577436536296771",
            "extra": "mean: 9.902051474750058 msec\nrounds: 99"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[ethanol_100]",
            "value": 51.8945300943006,
            "unit": "iter/sec",
            "range": "stddev: 0.0002266689708400492",
            "extra": "mean: 19.269853647057623 msec\nrounds: 51"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[ethanol_1000]",
            "value": 5.349572419286103,
            "unit": "iter/sec",
            "range": "stddev: 0.0017307482943244633",
            "extra": "mean: 186.93082766668093 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[periodic_100]",
            "value": 52.85746296135652,
            "unit": "iter/sec",
            "range": "stddev: 0.0001770490931674957",
            "extra": "mean: 18.918804346154268 msec\nrounds: 52"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[periodic_1000]",
            "value": 5.423452927105112,
            "unit": "iter/sec",
            "range": "stddev: 0.0012982095385271374",
            "extra": "mean: 184.38437899999846 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[ethanol_100]",
            "value": 377.9483777034267,
            "unit": "iter/sec",
            "range": "stddev: 0.00005678270855077141",
            "extra": "mean: 2.645863983003236 msec\nrounds: 353"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[ethanol_1000]",
            "value": 37.5899543806616,
            "unit": "iter/sec",
            "range": "stddev: 0.00017847071810341627",
            "extra": "mean: 26.602852184211656 msec\nrounds: 38"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[periodic_100]",
            "value": 416.3558584964941,
            "unit": "iter/sec",
            "range": "stddev: 0.00012337194640383054",
            "extra": "mean: 2.4017915914792405 msec\nrounds: 399"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[periodic_1000]",
            "value": 38.308694214239424,
            "unit": "iter/sec",
            "range": "stddev: 0.003952194955039276",
            "extra": "mean: 26.10373494871819 msec\nrounds: 39"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[ethanol_100]",
            "value": 1.4073128485768294,
            "unit": "iter/sec",
            "range": "stddev: 0.011375127435688907",
            "extra": "mean: 710.5740567999987 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[ethanol_1000]",
            "value": 0.1382277016320716,
            "unit": "iter/sec",
            "range": "stddev: 0.08574953185854156",
            "extra": "mean: 7.234439900200004 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[periodic_100]",
            "value": 1.4945901177906395,
            "unit": "iter/sec",
            "range": "stddev: 0.009512483327143067",
            "extra": "mean: 669.0797618000033 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[periodic_1000]",
            "value": 0.14726714279144582,
            "unit": "iter/sec",
            "range": "stddev: 0.061680541467359906",
            "extra": "mean: 6.790380943399998 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[ethanol_100]",
            "value": 11.600990890515503,
            "unit": "iter/sec",
            "range": "stddev: 0.0009225558739116115",
            "extra": "mean: 86.19953325000533 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[ethanol_1000]",
            "value": 1.1394278941021028,
            "unit": "iter/sec",
            "range": "stddev: 0.020924829914563653",
            "extra": "mean: 877.6334204000023 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[periodic_100]",
            "value": 15.220325211732858,
            "unit": "iter/sec",
            "range": "stddev: 0.00035568525574757574",
            "extra": "mean: 65.70161846667588 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[periodic_1000]",
            "value": 1.5143766026782426,
            "unit": "iter/sec",
            "range": "stddev: 0.0022137721063728295",
            "extra": "mean: 660.3377245999809 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[ethanol_100]",
            "value": 23.41138677001111,
            "unit": "iter/sec",
            "range": "stddev: 0.003849439203458204",
            "extra": "mean: 42.71425737500323 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.560445346083787,
            "unit": "iter/sec",
            "range": "stddev: 0.002640326626842486",
            "extra": "mean: 390.55705739999667 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[periodic_100]",
            "value": 25.568260338888923,
            "unit": "iter/sec",
            "range": "stddev: 0.0005596096319705753",
            "extra": "mean: 39.11099100000229 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[periodic_1000]",
            "value": 2.5388866272572232,
            "unit": "iter/sec",
            "range": "stddev: 0.0036320620985840226",
            "extra": "mean: 393.87343619998774 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[ethanol_100]",
            "value": 37.55950631256774,
            "unit": "iter/sec",
            "range": "stddev: 0.0009484114459397596",
            "extra": "mean: 26.62441810810999 msec\nrounds: 37"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[ethanol_1000]",
            "value": 3.6718970892149287,
            "unit": "iter/sec",
            "range": "stddev: 0.009828685070961752",
            "extra": "mean: 272.33878719999893 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[periodic_100]",
            "value": 34.01773392093631,
            "unit": "iter/sec",
            "range": "stddev: 0.0038053550644536263",
            "extra": "mean: 29.396431941180747 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[periodic_1000]",
            "value": 3.8413686797834155,
            "unit": "iter/sec",
            "range": "stddev: 0.005167788631235953",
            "extra": "mean: 260.3238802000078 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[ethanol_100]",
            "value": 136.1236771647655,
            "unit": "iter/sec",
            "range": "stddev: 0.00019673720746807573",
            "extra": "mean: 7.346260553846115 msec\nrounds: 130"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[ethanol_1000]",
            "value": 13.408674786976414,
            "unit": "iter/sec",
            "range": "stddev: 0.0010526423163611173",
            "extra": "mean: 74.57858557143027 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[periodic_100]",
            "value": 83.44279041904089,
            "unit": "iter/sec",
            "range": "stddev: 0.0009376694551009783",
            "extra": "mean: 11.984258855415854 msec\nrounds: 83"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[periodic_1000]",
            "value": 8.32357451253706,
            "unit": "iter/sec",
            "range": "stddev: 0.0018821773813372145",
            "extra": "mean: 120.14069177776794 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[ethanol_100]",
            "value": 2.1164430154876466,
            "unit": "iter/sec",
            "range": "stddev: 0.014809209392845345",
            "extra": "mean: 472.4908691999872 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[ethanol_1000]",
            "value": 0.21148609493289988,
            "unit": "iter/sec",
            "range": "stddev: 0.053831585715350044",
            "extra": "mean: 4.728443259199992 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[periodic_100]",
            "value": 2.4509691669584273,
            "unit": "iter/sec",
            "range": "stddev: 0.0010603209054779624",
            "extra": "mean: 408.0018685999903 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[periodic_1000]",
            "value": 0.24054892265004782,
            "unit": "iter/sec",
            "range": "stddev: 0.03530609098472372",
            "extra": "mean: 4.157158506399992 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[ethanol_100]",
            "value": 24.41439183202461,
            "unit": "iter/sec",
            "range": "stddev: 0.0018510555409709144",
            "extra": "mean: 40.95944748000193 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[ethanol_1000]",
            "value": 2.371515695386142,
            "unit": "iter/sec",
            "range": "stddev: 0.025822309666141737",
            "extra": "mean: 421.67125520001036 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[periodic_100]",
            "value": 24.545071266585406,
            "unit": "iter/sec",
            "range": "stddev: 0.0004577166600627699",
            "extra": "mean: 40.741376919991126 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[periodic_1000]",
            "value": 2.4476547145032415,
            "unit": "iter/sec",
            "range": "stddev: 0.005964890741310201",
            "extra": "mean: 408.55435779999425 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[ethanol_100]",
            "value": 9679.966812056753,
            "unit": "iter/sec",
            "range": "stddev: 0.000005262349455319069",
            "extra": "mean: 103.30613930974054 usec\nrounds: 4953"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[ethanol_1000]",
            "value": 845.0847066615479,
            "unit": "iter/sec",
            "range": "stddev: 0.00001668992788885995",
            "extra": "mean: 1.1833133319267306 msec\nrounds: 711"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[periodic_100]",
            "value": 9391.209370897515,
            "unit": "iter/sec",
            "range": "stddev: 0.0000049233083255120055",
            "extra": "mean: 106.48255836984181 usec\nrounds: 5448"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[periodic_1000]",
            "value": 800.7353914291002,
            "unit": "iter/sec",
            "range": "stddev: 0.00018582705614875574",
            "extra": "mean: 1.2488520061730572 msec\nrounds: 648"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[ethanol_100]",
            "value": 710.4947281956142,
            "unit": "iter/sec",
            "range": "stddev: 0.00026007375417394166",
            "extra": "mean: 1.4074699787563785 msec\nrounds: 659"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[ethanol_1000]",
            "value": 99.4333190740963,
            "unit": "iter/sec",
            "range": "stddev: 0.0003404801598124037",
            "extra": "mean: 10.056991050000192 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[periodic_100]",
            "value": 731.7305589039721,
            "unit": "iter/sec",
            "range": "stddev: 0.0000863589504441465",
            "extra": "mean: 1.3666232574704236 msec\nrounds: 703"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[periodic_1000]",
            "value": 97.59626951049421,
            "unit": "iter/sec",
            "range": "stddev: 0.000543805734695257",
            "extra": "mean: 10.246293275507558 msec\nrounds: 98"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[ethanol_100]",
            "value": 3331.9470622873187,
            "unit": "iter/sec",
            "range": "stddev: 0.000012482856022436124",
            "extra": "mean: 300.1248163029094 usec\nrounds: 2564"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[ethanol_1000]",
            "value": 473.43106770352244,
            "unit": "iter/sec",
            "range": "stddev: 0.000022614586029305385",
            "extra": "mean: 2.1122399187926377 msec\nrounds: 431"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[periodic_100]",
            "value": 3314.9428065261973,
            "unit": "iter/sec",
            "range": "stddev: 0.000012802205051236579",
            "extra": "mean: 301.6643297830898 usec\nrounds: 2629"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[periodic_1000]",
            "value": 428.1130176387453,
            "unit": "iter/sec",
            "range": "stddev: 0.0005558148723746897",
            "extra": "mean: 2.3358317986112493 msec\nrounds: 432"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[ethanol_100]",
            "value": 926.365167879092,
            "unit": "iter/sec",
            "range": "stddev: 0.00003816903752425988",
            "extra": "mean: 1.0794879111112248 msec\nrounds: 180"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[ethanol_1000]",
            "value": 247.32135206149798,
            "unit": "iter/sec",
            "range": "stddev: 0.00008658632061790995",
            "extra": "mean: 4.0433225504579315 msec\nrounds: 109"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[periodic_100]",
            "value": 922.0269714502085,
            "unit": "iter/sec",
            "range": "stddev: 0.000049945487302061133",
            "extra": "mean: 1.0845669714272583 msec\nrounds: 175"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[periodic_1000]",
            "value": 246.3354463939062,
            "unit": "iter/sec",
            "range": "stddev: 0.00013925582344225093",
            "extra": "mean: 4.059505096156302 msec\nrounds: 104"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[ethanol_100]",
            "value": 377.6279187583606,
            "unit": "iter/sec",
            "range": "stddev: 0.00007728562773095258",
            "extra": "mean: 2.6481092904571173 msec\nrounds: 241"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[ethanol_1000]",
            "value": 54.6196769340124,
            "unit": "iter/sec",
            "range": "stddev: 0.0003122846606864404",
            "extra": "mean: 18.308420264150016 msec\nrounds: 53"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[periodic_100]",
            "value": 371.45668644688567,
            "unit": "iter/sec",
            "range": "stddev: 0.00022806995525162963",
            "extra": "mean: 2.692103915439921 msec\nrounds: 272"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[periodic_1000]",
            "value": 48.48797540202755,
            "unit": "iter/sec",
            "range": "stddev: 0.01691422955190143",
            "extra": "mean: 20.623669924526986 msec\nrounds: 53"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[ethanol_100]",
            "value": 144.23697664440382,
            "unit": "iter/sec",
            "range": "stddev: 0.00009705581124868747",
            "extra": "mean: 6.933034948904682 msec\nrounds: 137"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[ethanol_1000]",
            "value": 14.211369186112673,
            "unit": "iter/sec",
            "range": "stddev: 0.0005172638676589683",
            "extra": "mean: 70.36619673333084 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[periodic_100]",
            "value": 86.95726507918901,
            "unit": "iter/sec",
            "range": "stddev: 0.00042393483159503816",
            "extra": "mean: 11.499901694117613 msec\nrounds: 85"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[periodic_1000]",
            "value": 8.758036727255247,
            "unit": "iter/sec",
            "range": "stddev: 0.0006312292131456022",
            "extra": "mean: 114.18084111111033 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[ethanol_100]",
            "value": 2582.034318326739,
            "unit": "iter/sec",
            "range": "stddev: 0.00001603240562847663",
            "extra": "mean: 387.291521612323 usec\nrounds: 2059"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[ethanol_1000]",
            "value": 2060.3656742498133,
            "unit": "iter/sec",
            "range": "stddev: 0.000018676111447324566",
            "extra": "mean: 485.3507377345061 usec\nrounds: 1651"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[periodic_100]",
            "value": 2618.603772398662,
            "unit": "iter/sec",
            "range": "stddev: 0.00001485998067665008",
            "extra": "mean: 381.8828990244645 usec\nrounds: 2258"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[periodic_1000]",
            "value": 2042.5127311430767,
            "unit": "iter/sec",
            "range": "stddev: 0.000029116208070270303",
            "extra": "mean: 489.5930315403017 usec\nrounds: 1617"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[ethanol_100]",
            "value": 61.76821161851748,
            "unit": "iter/sec",
            "range": "stddev: 0.0001346377871541437",
            "extra": "mean: 16.189557278686213 msec\nrounds: 61"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[ethanol_1000]",
            "value": 5.945100933630638,
            "unit": "iter/sec",
            "range": "stddev: 0.022324786531280984",
            "extra": "mean: 168.2057228571401 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[periodic_100]",
            "value": 61.9647925008667,
            "unit": "iter/sec",
            "range": "stddev: 0.00046239214947234813",
            "extra": "mean: 16.138196540979507 msec\nrounds: 61"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[periodic_1000]",
            "value": 6.227706750431577,
            "unit": "iter/sec",
            "range": "stddev: 0.0034424595424047697",
            "extra": "mean: 160.57275014285162 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 240.8204996102598,
            "unit": "iter/sec",
            "range": "stddev: 0.0011883291793280998",
            "extra": "mean: 4.152470415178046 msec\nrounds: 224"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 19.174898532419324,
            "unit": "iter/sec",
            "range": "stddev: 0.040855918029340264",
            "extra": "mean: 52.15151456000058 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[periodic_100]",
            "value": 246.14166830051326,
            "unit": "iter/sec",
            "range": "stddev: 0.009008309266687104",
            "extra": "mean: 4.06270099209332 msec\nrounds: 253"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 24.06925774873474,
            "unit": "iter/sec",
            "range": "stddev: 0.027430089305976322",
            "extra": "mean: 41.54677350000822 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[ethanol_100]",
            "value": 22.19744715817174,
            "unit": "iter/sec",
            "range": "stddev: 0.005021505056392601",
            "extra": "mean: 45.0502255000013 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 2.8355878525232687,
            "unit": "iter/sec",
            "range": "stddev: 0.0018590735170805185",
            "extra": "mean: 352.66055999998116 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[periodic_100]",
            "value": 11.204957850772434,
            "unit": "iter/sec",
            "range": "stddev: 0.000704785806609115",
            "extra": "mean: 89.24620809091782 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[periodic_1000]",
            "value": 1.1298615269665258,
            "unit": "iter/sec",
            "range": "stddev: 0.09520213693303452",
            "extra": "mean: 885.0642102000052 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[ethanol_100]",
            "value": 212.79161508075234,
            "unit": "iter/sec",
            "range": "stddev: 0.0003365759114614922",
            "extra": "mean: 4.699433291206093 msec\nrounds: 182"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 20.48273611934606,
            "unit": "iter/sec",
            "range": "stddev: 0.03098920769340263",
            "extra": "mean: 48.82160245454192 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[periodic_100]",
            "value": 236.02803981457114,
            "unit": "iter/sec",
            "range": "stddev: 0.0004081540435538287",
            "extra": "mean: 4.236784751445727 msec\nrounds: 173"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[periodic_1000]",
            "value": 27.635234967139485,
            "unit": "iter/sec",
            "range": "stddev: 0.002512735782773869",
            "extra": "mean: 36.185688350002465 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 265.24562208792224,
            "unit": "iter/sec",
            "range": "stddev: 0.000510054736185806",
            "extra": "mean: 3.7700904999989984 msec\nrounds: 254"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 24.0296481511101,
            "unit": "iter/sec",
            "range": "stddev: 0.029927551046429645",
            "extra": "mean: 41.615257689647144 msec\nrounds: 29"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[periodic_100]",
            "value": 270.9733949648813,
            "unit": "iter/sec",
            "range": "stddev: 0.0005767006296513281",
            "extra": "mean: 3.6903992000011736 msec\nrounds: 260"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 25.626273428421552,
            "unit": "iter/sec",
            "range": "stddev: 0.009559371038952083",
            "extra": "mean: 39.02245103226447 msec\nrounds: 31"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[ethanol_100]",
            "value": 134.65282573308926,
            "unit": "iter/sec",
            "range": "stddev: 0.0013473581695379832",
            "extra": "mean: 7.426505864661276 msec\nrounds: 133"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[ethanol_1000]",
            "value": 11.872217638669113,
            "unit": "iter/sec",
            "range": "stddev: 0.05433851824998838",
            "extra": "mean: 84.23026181249327 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[periodic_100]",
            "value": 147.39469305428668,
            "unit": "iter/sec",
            "range": "stddev: 0.0006856180058620643",
            "extra": "mean: 6.784504782893994 msec\nrounds: 152"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[periodic_1000]",
            "value": 16.69592403103941,
            "unit": "iter/sec",
            "range": "stddev: 0.0023165884595145944",
            "extra": "mean: 59.894858058823154 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[ethanol_100]",
            "value": 58.56155499052888,
            "unit": "iter/sec",
            "range": "stddev: 0.0007469109638355243",
            "extra": "mean: 17.07604929824232 msec\nrounds: 57"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[ethanol_1000]",
            "value": 5.198017902902643,
            "unit": "iter/sec",
            "range": "stddev: 0.0514477119163406",
            "extra": "mean: 192.38102266665655 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[periodic_100]",
            "value": 44.050589062049184,
            "unit": "iter/sec",
            "range": "stddev: 0.0011200964403126578",
            "extra": "mean: 22.701172022726205 msec\nrounds: 44"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[periodic_1000]",
            "value": 4.470159072255188,
            "unit": "iter/sec",
            "range": "stddev: 0.0021996494572878666",
            "extra": "mean: 223.70568560002084 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[ethanol_100]",
            "value": 2.1513671756826005,
            "unit": "iter/sec",
            "range": "stddev: 0.0015219190451179177",
            "extra": "mean: 464.8207016000015 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[ethanol_1000]",
            "value": 0.21520267996521708,
            "unit": "iter/sec",
            "range": "stddev: 0.03615359856583895",
            "extra": "mean: 4.646782280599984 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[periodic_100]",
            "value": 2.433808164730704,
            "unit": "iter/sec",
            "range": "stddev: 0.0011311014419516361",
            "extra": "mean: 410.87872680000146 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[periodic_1000]",
            "value": 0.23626300662074237,
            "unit": "iter/sec",
            "range": "stddev: 0.10933924720887164",
            "extra": "mean: 4.232571210799984 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[ethanol_100]",
            "value": 18.326006234343957,
            "unit": "iter/sec",
            "range": "stddev: 0.0009099257534419812",
            "extra": "mean: 54.567262894735045 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[ethanol_1000]",
            "value": 1.8302249271470323,
            "unit": "iter/sec",
            "range": "stddev: 0.0016525895997714921",
            "extra": "mean: 546.3809311999739 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[periodic_100]",
            "value": 18.274593445577807,
            "unit": "iter/sec",
            "range": "stddev: 0.0003748562644539049",
            "extra": "mean: 54.72077958823133 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[periodic_1000]",
            "value": 1.7725273356400586,
            "unit": "iter/sec",
            "range": "stddev: 0.02043794383975494",
            "extra": "mean: 564.1661935999991 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[ethanol_100]",
            "value": 211.20262859969418,
            "unit": "iter/sec",
            "range": "stddev: 0.0007297136859683945",
            "extra": "mean: 4.734789555556924 msec\nrounds: 198"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[ethanol_1000]",
            "value": 20.97032882172254,
            "unit": "iter/sec",
            "range": "stddev: 0.002084831933914029",
            "extra": "mean: 47.686424399989846 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[periodic_100]",
            "value": 240.4320594764681,
            "unit": "iter/sec",
            "range": "stddev: 0.0003837859507411737",
            "extra": "mean: 4.159179113540278 msec\nrounds: 229"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[periodic_1000]",
            "value": 23.030900163383333,
            "unit": "iter/sec",
            "range": "stddev: 0.0032143171285852062",
            "extra": "mean: 43.419926833337286 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[ethanol_100]",
            "value": 1.3602259584945047,
            "unit": "iter/sec",
            "range": "stddev: 0.026644168287508728",
            "extra": "mean: 735.1719718000368 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[ethanol_1000]",
            "value": 0.1407244309236744,
            "unit": "iter/sec",
            "range": "stddev: 0.10995114448749368",
            "extra": "mean: 7.106086650599968 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[periodic_100]",
            "value": 1.494839308405272,
            "unit": "iter/sec",
            "range": "stddev: 0.041198770831313014",
            "extra": "mean: 668.9682258000175 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[periodic_1000]",
            "value": 0.1491880085389662,
            "unit": "iter/sec",
            "range": "stddev: 0.040919167628236115",
            "extra": "mean: 6.702951596399998 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[ethanol_100]",
            "value": 10.288224439312012,
            "unit": "iter/sec",
            "range": "stddev: 0.018011683895757667",
            "extra": "mean: 97.19850163638841 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[ethanol_1000]",
            "value": 1.1282079854525913,
            "unit": "iter/sec",
            "range": "stddev: 0.006416280764312943",
            "extra": "mean: 886.3613916000077 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[periodic_100]",
            "value": 14.545902707359112,
            "unit": "iter/sec",
            "range": "stddev: 0.0025517624138585555",
            "extra": "mean: 68.74788180001208 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[periodic_1000]",
            "value": 1.432623314225861,
            "unit": "iter/sec",
            "range": "stddev: 0.024245058959722107",
            "extra": "mean: 698.0201913999736 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[ethanol_100]",
            "value": 23.32106528018192,
            "unit": "iter/sec",
            "range": "stddev: 0.0011052596505276217",
            "extra": "mean: 42.87968786956714 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.1352482549436793,
            "unit": "iter/sec",
            "range": "stddev: 0.08238021963197238",
            "extra": "mean: 468.3296182000049 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[periodic_100]",
            "value": 23.27459992090846,
            "unit": "iter/sec",
            "range": "stddev: 0.0012297173704774954",
            "extra": "mean: 42.96529278261242 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[periodic_1000]",
            "value": 2.2482386126252125,
            "unit": "iter/sec",
            "range": "stddev: 0.03044113290411615",
            "extra": "mean: 444.7926454000026 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[ethanol_100]",
            "value": 33.101600862028214,
            "unit": "iter/sec",
            "range": "stddev: 0.0017210422058020257",
            "extra": "mean: 30.21001927272733 msec\nrounds: 33"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[ethanol_1000]",
            "value": 3.170771119537877,
            "unit": "iter/sec",
            "range": "stddev: 0.005759663887566493",
            "extra": "mean: 315.38069520001955 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[periodic_100]",
            "value": 33.46706129576191,
            "unit": "iter/sec",
            "range": "stddev: 0.0012670748712457591",
            "extra": "mean: 29.880125749990327 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[periodic_1000]",
            "value": 3.3092658962603774,
            "unit": "iter/sec",
            "range": "stddev: 0.004902524321309472",
            "extra": "mean: 302.18182260000503 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[ethanol_100]",
            "value": 58.38102394040539,
            "unit": "iter/sec",
            "range": "stddev: 0.00042522668318920997",
            "extra": "mean: 17.128853392855653 msec\nrounds: 56"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[ethanol_1000]",
            "value": 5.82178526530943,
            "unit": "iter/sec",
            "range": "stddev: 0.0008004788631541814",
            "extra": "mean: 171.7686163999815 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[periodic_100]",
            "value": 43.960582304257535,
            "unit": "iter/sec",
            "range": "stddev: 0.001121494387084301",
            "extra": "mean: 22.74765136364336 msec\nrounds: 44"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[periodic_1000]",
            "value": 4.455412731983994,
            "unit": "iter/sec",
            "range": "stddev: 0.002717224904006773",
            "extra": "mean: 224.44609739998214 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[ethanol_100]",
            "value": 2.159513543314758,
            "unit": "iter/sec",
            "range": "stddev: 0.002926108673745519",
            "extra": "mean: 463.067250999984 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[ethanol_1000]",
            "value": 0.21489258423315916,
            "unit": "iter/sec",
            "range": "stddev: 0.015638163757403147",
            "extra": "mean: 4.653487711400021 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[periodic_100]",
            "value": 2.4370770111657984,
            "unit": "iter/sec",
            "range": "stddev: 0.0008505010265889453",
            "extra": "mean: 410.3276159999723 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[periodic_1000]",
            "value": 0.23794261288812527,
            "unit": "iter/sec",
            "range": "stddev: 0.09852042622489392",
            "extra": "mean: 4.2026940355999844 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[ethanol_100]",
            "value": 18.22513647100033,
            "unit": "iter/sec",
            "range": "stddev: 0.0016826688686319893",
            "extra": "mean: 54.86927363156874 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[ethanol_1000]",
            "value": 1.8218601146661435,
            "unit": "iter/sec",
            "range": "stddev: 0.002483049371915638",
            "extra": "mean: 548.8895618000015 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[periodic_100]",
            "value": 18.176168141693985,
            "unit": "iter/sec",
            "range": "stddev: 0.0010024661214596826",
            "extra": "mean: 55.01709668420805 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[periodic_1000]",
            "value": 1.7119015245766531,
            "unit": "iter/sec",
            "range": "stddev: 0.08178199651740377",
            "extra": "mean: 584.145750000016 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 230.31199951819033,
            "unit": "iter/sec",
            "range": "stddev: 0.0015788560100695956",
            "extra": "mean: 4.341936165254033 msec\nrounds: 236"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 18.945165253881644,
            "unit": "iter/sec",
            "range": "stddev: 0.04277011659012719",
            "extra": "mean: 52.783915400004844 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[periodic_100]",
            "value": 240.18403149581272,
            "unit": "iter/sec",
            "range": "stddev: 0.00981868193704653",
            "extra": "mean: 4.163474123455346 msec\nrounds: 243"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 22.35327465830351,
            "unit": "iter/sec",
            "range": "stddev: 0.03205067486237465",
            "extra": "mean: 44.736174689668246 msec\nrounds: 29"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[ethanol_100]",
            "value": 24.103280822897943,
            "unit": "iter/sec",
            "range": "stddev: 0.0015976565960812076",
            "extra": "mean: 41.48812799998609 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 2.5775761866669455,
            "unit": "iter/sec",
            "range": "stddev: 0.06652886679450697",
            "extra": "mean: 387.96137439999256 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[periodic_100]",
            "value": 11.098781567155951,
            "unit": "iter/sec",
            "range": "stddev: 0.00118506444995188",
            "extra": "mean: 90.09998025001664 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[periodic_1000]",
            "value": 1.1506444318996019,
            "unit": "iter/sec",
            "range": "stddev: 0.040330652075244736",
            "extra": "mean: 869.0782072000275 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[ethanol_100]",
            "value": 189.5867472246516,
            "unit": "iter/sec",
            "range": "stddev: 0.0003820863201567157",
            "extra": "mean: 5.2746302926704365 msec\nrounds: 164"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 19.719245061397267,
            "unit": "iter/sec",
            "range": "stddev: 0.031972362506925235",
            "extra": "mean: 50.711880545448324 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[periodic_100]",
            "value": 222.49542676966814,
            "unit": "iter/sec",
            "range": "stddev: 0.0005914337156388022",
            "extra": "mean: 4.49447440119846 msec\nrounds: 167"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[periodic_1000]",
            "value": 22.109134850801627,
            "unit": "iter/sec",
            "range": "stddev: 0.03123271765634989",
            "extra": "mean: 45.23017326314522 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 236.70741167515754,
            "unit": "iter/sec",
            "range": "stddev: 0.0011925078064598791",
            "extra": "mean: 4.224624792789917 msec\nrounds: 222"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 21.048675708067794,
            "unit": "iter/sec",
            "range": "stddev: 0.03430812463904722",
            "extra": "mean: 47.50892711111074 msec\nrounds: 27"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[periodic_100]",
            "value": 197.22747468774938,
            "unit": "iter/sec",
            "range": "stddev: 0.012583140698758766",
            "extra": "mean: 5.070287502201204 msec\nrounds: 227"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 26.29793475099986,
            "unit": "iter/sec",
            "range": "stddev: 0.004044922223612155",
            "extra": "mean: 38.025799724139155 msec\nrounds: 29"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[ethanol_100]",
            "value": 99.5612911679916,
            "unit": "iter/sec",
            "range": "stddev: 0.020116536826495793",
            "extra": "mean: 10.04406419672362 msec\nrounds: 61"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[ethanol_1000]",
            "value": 10.951569338531609,
            "unit": "iter/sec",
            "range": "stddev: 0.04688140085077222",
            "extra": "mean: 91.31111433332535 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[periodic_100]",
            "value": 138.19698454537303,
            "unit": "iter/sec",
            "range": "stddev: 0.000613234546769278",
            "extra": "mean: 7.236047901404668 msec\nrounds: 142"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[periodic_1000]",
            "value": 12.081062275179484,
            "unit": "iter/sec",
            "range": "stddev: 0.04469194980032361",
            "extra": "mean: 82.77417806665046 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[ethanol_100]",
            "value": 58.559415297373704,
            "unit": "iter/sec",
            "range": "stddev: 0.0012819933507280665",
            "extra": "mean: 17.076673237289793 msec\nrounds: 59"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[ethanol_1000]",
            "value": 5.756312193265328,
            "unit": "iter/sec",
            "range": "stddev: 0.0035618831348503727",
            "extra": "mean: 173.72233583334187 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[periodic_100]",
            "value": 35.41793984812556,
            "unit": "iter/sec",
            "range": "stddev: 0.03128122776896152",
            "extra": "mean: 28.234279133344998 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[periodic_1000]",
            "value": 4.486964342416783,
            "unit": "iter/sec",
            "range": "stddev: 0.005105616538450349",
            "extra": "mean: 222.86782859998766 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[ethanol_100]",
            "value": 49.511439752102,
            "unit": "iter/sec",
            "range": "stddev: 0.0012504234123845907",
            "extra": "mean: 20.197352470598375 msec\nrounds: 51"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[ethanol_1000]",
            "value": 6.696732489851844,
            "unit": "iter/sec",
            "range": "stddev: 0.008411942268115653",
            "extra": "mean: 149.32655612500412 msec\nrounds: 8"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[periodic_100]",
            "value": 53.277769965754146,
            "unit": "iter/sec",
            "range": "stddev: 0.0013895369627119326",
            "extra": "mean: 18.769554368412553 msec\nrounds: 57"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[periodic_1000]",
            "value": 7.228228007791285,
            "unit": "iter/sec",
            "range": "stddev: 0.005251529858741916",
            "extra": "mean: 138.34649362500784 msec\nrounds: 8"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[ethanol_100]",
            "value": 29.418683230300537,
            "unit": "iter/sec",
            "range": "stddev: 0.002453700056170839",
            "extra": "mean: 33.992004066654616 msec\nrounds: 30"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[ethanol_1000]",
            "value": 3.023173641140757,
            "unit": "iter/sec",
            "range": "stddev: 0.005143399932023192",
            "extra": "mean: 330.77822140003263 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[periodic_100]",
            "value": 28.43104287807252,
            "unit": "iter/sec",
            "range": "stddev: 0.0014579225709956515",
            "extra": "mean: 35.17282163332993 msec\nrounds: 30"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[periodic_1000]",
            "value": 2.967037974675811,
            "unit": "iter/sec",
            "range": "stddev: 0.0064100241758614515",
            "extra": "mean: 337.0364681999945 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[ethanol_100]",
            "value": 32.00334140487572,
            "unit": "iter/sec",
            "range": "stddev: 0.0014428598321143732",
            "extra": "mean: 31.246737249993828 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[ethanol_1000]",
            "value": 2.8705302441800606,
            "unit": "iter/sec",
            "range": "stddev: 0.08447765399751289",
            "extra": "mean: 348.36769340001865 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[periodic_100]",
            "value": 32.00366341364764,
            "unit": "iter/sec",
            "range": "stddev: 0.0008258183456840545",
            "extra": "mean: 31.24642285712704 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[periodic_1000]",
            "value": 3.205049835496126,
            "unit": "iter/sec",
            "range": "stddev: 0.0022426728485884224",
            "extra": "mean: 312.0076290000043 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[ethanol_100]",
            "value": 209.72349997127785,
            "unit": "iter/sec",
            "range": "stddev: 0.0007388690211713675",
            "extra": "mean: 4.76818287000242 msec\nrounds: 200"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[ethanol_1000]",
            "value": 18.033336532472422,
            "unit": "iter/sec",
            "range": "stddev: 0.038753425736301784",
            "extra": "mean: 55.452855227279294 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[periodic_100]",
            "value": 212.74092565948396,
            "unit": "iter/sec",
            "range": "stddev: 0.0013094187565340185",
            "extra": "mean: 4.700553017244147 msec\nrounds: 232"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[periodic_1000]",
            "value": 23.612393540099774,
            "unit": "iter/sec",
            "range": "stddev: 0.002788620453953535",
            "extra": "mean: 42.350640916675765 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[ethanol_100]",
            "value": 1.4129839847237455,
            "unit": "iter/sec",
            "range": "stddev: 0.01513196396743119",
            "extra": "mean: 707.7221050000162 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[ethanol_1000]",
            "value": 0.1402607396572209,
            "unit": "iter/sec",
            "range": "stddev: 0.041530800434289125",
            "extra": "mean: 7.129578828999979 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[periodic_100]",
            "value": 1.504626480571776,
            "unit": "iter/sec",
            "range": "stddev: 0.015997922172622265",
            "extra": "mean: 664.6167756000068 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[periodic_1000]",
            "value": 0.1501759659263378,
            "unit": "iter/sec",
            "range": "stddev: 0.04942980458897029",
            "extra": "mean: 6.658855122600016 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[ethanol_100]",
            "value": 11.393987659331213,
            "unit": "iter/sec",
            "range": "stddev: 0.0018456641278699018",
            "extra": "mean: 87.76558566666874 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[ethanol_1000]",
            "value": 1.076300707198209,
            "unit": "iter/sec",
            "range": "stddev: 0.0805137407317596",
            "extra": "mean: 929.1083740000204 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[periodic_100]",
            "value": 14.638014980112034,
            "unit": "iter/sec",
            "range": "stddev: 0.0009710759343136718",
            "extra": "mean: 68.31527371427423 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[periodic_1000]",
            "value": 1.4709925488449076,
            "unit": "iter/sec",
            "range": "stddev: 0.0037637689663005416",
            "extra": "mean: 679.8130968000123 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[ethanol_100]",
            "value": 21.43858190141633,
            "unit": "iter/sec",
            "range": "stddev: 0.005215305417413164",
            "extra": "mean: 46.64487626086572 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.3045912054471187,
            "unit": "iter/sec",
            "range": "stddev: 0.005143779899092298",
            "extra": "mean: 433.91643500001464 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[periodic_100]",
            "value": 23.232527666817024,
            "unit": "iter/sec",
            "range": "stddev: 0.001227547660049048",
            "extra": "mean: 43.04309950002979 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[periodic_1000]",
            "value": 2.332294453661769,
            "unit": "iter/sec",
            "range": "stddev: 0.002529909567292387",
            "extra": "mean: 428.76232820001405 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[ethanol_100]",
            "value": 32.20180842897058,
            "unit": "iter/sec",
            "range": "stddev: 0.0014041945168691212",
            "extra": "mean: 31.054156545454852 msec\nrounds: 33"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[ethanol_1000]",
            "value": 3.0240083114167104,
            "unit": "iter/sec",
            "range": "stddev: 0.03470196990287351",
            "extra": "mean: 330.68692179999744 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[periodic_100]",
            "value": 33.22859200112174,
            "unit": "iter/sec",
            "range": "stddev: 0.0014825836795076674",
            "extra": "mean: 30.09456434284792 msec\nrounds: 35"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[periodic_1000]",
            "value": 3.3154490078873464,
            "unit": "iter/sec",
            "range": "stddev: 0.006304541003966589",
            "extra": "mean: 301.6182717999982 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[ethanol_100]",
            "value": 58.204490126173546,
            "unit": "iter/sec",
            "range": "stddev: 0.0012018450030907115",
            "extra": "mean: 17.18080508620962 msec\nrounds: 58"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[ethanol_1000]",
            "value": 5.880153440957914,
            "unit": "iter/sec",
            "range": "stddev: 0.0013932609277065404",
            "extra": "mean: 170.06358933332422 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[periodic_100]",
            "value": 44.665872607379235,
            "unit": "iter/sec",
            "range": "stddev: 0.0006633520504378954",
            "extra": "mean: 22.38845771110694 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[periodic_1000]",
            "value": 4.368404642191124,
            "unit": "iter/sec",
            "range": "stddev: 0.011457576963018962",
            "extra": "mean: 228.91652259997954 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[ethanol_100]",
            "value": 2.1560784304765614,
            "unit": "iter/sec",
            "range": "stddev: 0.0024023136861526994",
            "extra": "mean: 463.80502020001586 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[ethanol_1000]",
            "value": 0.216637148331524,
            "unit": "iter/sec",
            "range": "stddev: 0.02355495125174489",
            "extra": "mean: 4.616013494000026 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[periodic_100]",
            "value": 2.428637502152459,
            "unit": "iter/sec",
            "range": "stddev: 0.0009282085565119643",
            "extra": "mean: 411.75350340004115 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[periodic_1000]",
            "value": 0.23941683176407208,
            "unit": "iter/sec",
            "range": "stddev: 0.03847557400983993",
            "extra": "mean: 4.17681577620001 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[ethanol_100]",
            "value": 18.360212684694044,
            "unit": "iter/sec",
            "range": "stddev: 0.00028746770442525453",
            "extra": "mean: 54.46560000002876 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[ethanol_1000]",
            "value": 1.8204954739638124,
            "unit": "iter/sec",
            "range": "stddev: 0.002670772801683159",
            "extra": "mean: 549.3010085999686 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[periodic_100]",
            "value": 18.194198628849005,
            "unit": "iter/sec",
            "range": "stddev: 0.0008838708064071766",
            "extra": "mean: 54.96257463158528 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[periodic_1000]",
            "value": 1.765574396231919,
            "unit": "iter/sec",
            "range": "stddev: 0.01844465399478874",
            "extra": "mean: 566.387914400093 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 1555.2212444440834,
            "unit": "iter/sec",
            "range": "stddev: 0.00023284682809629508",
            "extra": "mean: 642.9953317397305 usec\nrounds: 838"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 198.21408356829377,
            "unit": "iter/sec",
            "range": "stddev: 0.00540106912843571",
            "extra": "mean: 5.045050190167009 msec\nrounds: 163"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[periodic_100]",
            "value": 980.8272272548943,
            "unit": "iter/sec",
            "range": "stddev: 0.002119569948669944",
            "extra": "mean: 1.019547553546985 msec\nrounds: 775"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 102.08646140636942,
            "unit": "iter/sec",
            "range": "stddev: 0.010769159719484717",
            "extra": "mean: 9.795618206603912 msec\nrounds: 121"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[ethanol_100]",
            "value": 706.7401380598737,
            "unit": "iter/sec",
            "range": "stddev: 0.00006058098383227826",
            "extra": "mean: 1.4149472290411809 msec\nrounds: 668"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 96.84123207145191,
            "unit": "iter/sec",
            "range": "stddev: 0.0003132046948879427",
            "extra": "mean: 10.326180064109208 msec\nrounds: 78"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[periodic_100]",
            "value": 701.5080008757632,
            "unit": "iter/sec",
            "range": "stddev: 0.00008488781082373007",
            "extra": "mean: 1.4255004914435747 msec\nrounds: 643"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[periodic_1000]",
            "value": 91.70891423987969,
            "unit": "iter/sec",
            "range": "stddev: 0.001227714880515627",
            "extra": "mean: 10.904065414887981 msec\nrounds: 94"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[ethanol_100]",
            "value": 4564.911206199494,
            "unit": "iter/sec",
            "range": "stddev: 0.000020425286385084133",
            "extra": "mean: 219.0623113636744 usec\nrounds: 3520"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 2195.414004399757,
            "unit": "iter/sec",
            "range": "stddev: 0.00002877167594174941",
            "extra": "mean: 455.4949535695468 usec\nrounds: 1680"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[periodic_100]",
            "value": 4680.276243539179,
            "unit": "iter/sec",
            "range": "stddev: 0.000012199092077866424",
            "extra": "mean: 213.6626019415918 usec\nrounds: 3404"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[periodic_1000]",
            "value": 2242.217819935659,
            "unit": "iter/sec",
            "range": "stddev: 0.000018427885001243684",
            "extra": "mean: 445.98700050858366 usec\nrounds: 1976"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 307.471416489264,
            "unit": "iter/sec",
            "range": "stddev: 0.00010208116902797896",
            "extra": "mean: 3.252334839505047 msec\nrounds: 162"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 39.54294466395411,
            "unit": "iter/sec",
            "range": "stddev: 0.000284200016554103",
            "extra": "mean: 25.28896136841228 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[periodic_100]",
            "value": 304.68970980379993,
            "unit": "iter/sec",
            "range": "stddev: 0.00007350830377201366",
            "extra": "mean: 3.2820274785253956 msec\nrounds: 163"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 39.1629599613657,
            "unit": "iter/sec",
            "range": "stddev: 0.00041926437456915415",
            "extra": "mean: 25.534331444469498 msec\nrounds: 18"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[ethanol_100]",
            "value": 491.0052624726129,
            "unit": "iter/sec",
            "range": "stddev: 0.00005968572896968879",
            "extra": "mean: 2.0366380493850156 msec\nrounds: 486"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[ethanol_1000]",
            "value": 73.72468633144341,
            "unit": "iter/sec",
            "range": "stddev: 0.0004282832057108623",
            "extra": "mean: 13.563977681835214 msec\nrounds: 66"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[periodic_100]",
            "value": 488.0740934548229,
            "unit": "iter/sec",
            "range": "stddev: 0.00013745645916478404",
            "extra": "mean: 2.0488692463095504 msec\nrounds: 475"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[periodic_1000]",
            "value": 72.78663386660247,
            "unit": "iter/sec",
            "range": "stddev: 0.0005049690526866629",
            "extra": "mean: 13.73878618748492 msec\nrounds: 64"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[ethanol_100]",
            "value": 14.55896306406623,
            "unit": "iter/sec",
            "range": "stddev: 0.008222252407023583",
            "extra": "mean: 68.68621038459494 msec\nrounds: 13"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[ethanol_1000]",
            "value": 1.5371119621989675,
            "unit": "iter/sec",
            "range": "stddev: 0.00996266052763083",
            "extra": "mean: 650.5706966000162 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[periodic_100]",
            "value": 11.404266454471426,
            "unit": "iter/sec",
            "range": "stddev: 0.0010207219907826545",
            "extra": "mean: 87.68648154550233 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[periodic_1000]",
            "value": 1.0794881433300338,
            "unit": "iter/sec",
            "range": "stddev: 0.03860717727760756",
            "extra": "mean: 926.3649686000008 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[ethanol_100]",
            "value": 5.5464721421483105,
            "unit": "iter/sec",
            "range": "stddev: 0.013070695747964888",
            "extra": "mean: 180.2947845714178 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[ethanol_1000]",
            "value": 0.5011429926048441,
            "unit": "iter/sec",
            "range": "stddev: 0.032964084806434105",
            "extra": "mean: 1.9954384571999981 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[periodic_100]",
            "value": 5.6827694860413525,
            "unit": "iter/sec",
            "range": "stddev: 0.0040863703202663896",
            "extra": "mean: 175.9705373333039 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[periodic_1000]",
            "value": 0.48980095249754774,
            "unit": "iter/sec",
            "range": "stddev: 0.0390345364747651",
            "extra": "mean: 2.0416456826000284 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 185.40040286257226,
            "unit": "iter/sec",
            "range": "stddev: 0.0013084219450213196",
            "extra": "mean: 5.393731537580575 msec\nrounds: 173"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 21.26784460253733,
            "unit": "iter/sec",
            "range": "stddev: 0.03288089189436282",
            "extra": "mean: 47.0193392272904 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[periodic_100]",
            "value": 222.69243300726455,
            "unit": "iter/sec",
            "range": "stddev: 0.00011717692023677263",
            "extra": "mean: 4.490498336633551 msec\nrounds: 202"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 22.83122912942053,
            "unit": "iter/sec",
            "range": "stddev: 0.027138804723477367",
            "extra": "mean: 43.799656791643805 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[ethanol_100]",
            "value": 10.274600092266466,
            "unit": "iter/sec",
            "range": "stddev: 0.0024885819629987945",
            "extra": "mean: 97.32738900005313 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 1.8242955506719392,
            "unit": "iter/sec",
            "range": "stddev: 0.00843043738749437",
            "extra": "mean: 548.1567938000353 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[periodic_100]",
            "value": 6.292212713498666,
            "unit": "iter/sec",
            "range": "stddev: 0.001376068436454632",
            "extra": "mean: 158.92660428575513 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[periodic_1000]",
            "value": 0.8074240747192851,
            "unit": "iter/sec",
            "range": "stddev: 0.0067065945190594905",
            "extra": "mean: 1.2385065435999878 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[ethanol_100]",
            "value": 25.821214417470017,
            "unit": "iter/sec",
            "range": "stddev: 0.00032835546274743185",
            "extra": "mean: 38.72784539999884 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 2.9302937130967703,
            "unit": "iter/sec",
            "range": "stddev: 0.020341337105531956",
            "extra": "mean: 341.26271899999665 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[periodic_100]",
            "value": 42.312691159153225,
            "unit": "iter/sec",
            "range": "stddev: 0.00020091737272437394",
            "extra": "mean: 23.633571219534133 msec\nrounds: 41"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[periodic_1000]",
            "value": 5.434353467056177,
            "unit": "iter/sec",
            "range": "stddev: 0.0012407355413795891",
            "extra": "mean: 184.01453016667801 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 61.79745658074229,
            "unit": "iter/sec",
            "range": "stddev: 0.000508894930606537",
            "extra": "mean: 16.18189574992357 msec\nrounds: 8"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 13.581005902726204,
            "unit": "iter/sec",
            "range": "stddev: 0.04480884293297069",
            "extra": "mean: 73.63224838885192 msec\nrounds: 18"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[periodic_100]",
            "value": 58.64222246911843,
            "unit": "iter/sec",
            "range": "stddev: 0.0017032702725254198",
            "extra": "mean: 17.052559706900773 msec\nrounds: 58"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 14.324835090593583,
            "unit": "iter/sec",
            "range": "stddev: 0.03996888085400906",
            "extra": "mean: 69.80883156251139 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[ethanol_100]",
            "value": 136.01526652843847,
            "unit": "iter/sec",
            "range": "stddev: 0.001286797325820011",
            "extra": "mean: 7.352115872896644 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[ethanol_1000]",
            "value": 14.678277301433907,
            "unit": "iter/sec",
            "range": "stddev: 0.03968288821814083",
            "extra": "mean: 68.12788581820232 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[periodic_100]",
            "value": 130.5858760127759,
            "unit": "iter/sec",
            "range": "stddev: 0.0015811262159130472",
            "extra": "mean: 7.657796007756342 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[periodic_1000]",
            "value": 18.415735467586252,
            "unit": "iter/sec",
            "range": "stddev: 0.0011934773545111477",
            "extra": "mean: 54.301388166663855 msec\nrounds: 18"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[ethanol_100]",
            "value": 9.193233203027305,
            "unit": "iter/sec",
            "range": "stddev: 0.012032096959751484",
            "extra": "mean: 108.77565900000263 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[ethanol_1000]",
            "value": 0.9662046093869652,
            "unit": "iter/sec",
            "range": "stddev: 0.017852911206696083",
            "extra": "mean: 1.0349774677999903 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[periodic_100]",
            "value": 7.089185692005973,
            "unit": "iter/sec",
            "range": "stddev: 0.003651089783108421",
            "extra": "mean: 141.0599247142922 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[periodic_1000]",
            "value": 0.7092477904467009,
            "unit": "iter/sec",
            "range": "stddev: 0.02398488247282446",
            "extra": "mean: 1.4099444699999366 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[ethanol_100]",
            "value": 50.414815104935926,
            "unit": "iter/sec",
            "range": "stddev: 0.000474088717094839",
            "extra": "mean: 19.835439204102006 msec\nrounds: 49"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[ethanol_1000]",
            "value": 16.546668732569223,
            "unit": "iter/sec",
            "range": "stddev: 0.0009433755685634358",
            "extra": "mean: 60.435125411780014 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[periodic_100]",
            "value": 48.80683692573079,
            "unit": "iter/sec",
            "range": "stddev: 0.0007776164913441459",
            "extra": "mean: 20.488932760008538 msec\nrounds: 50"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[periodic_1000]",
            "value": 11.953765024420298,
            "unit": "iter/sec",
            "range": "stddev: 0.0016251259909520332",
            "extra": "mean: 83.65565141669624 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[ethanol_100]",
            "value": 48.41122566672449,
            "unit": "iter/sec",
            "range": "stddev: 0.00028909087057544017",
            "extra": "mean: 20.656366085094827 msec\nrounds: 47"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[ethanol_1000]",
            "value": 4.914659527334315,
            "unit": "iter/sec",
            "range": "stddev: 0.0015816501216163275",
            "extra": "mean: 203.47289459996318 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[periodic_100]",
            "value": 32.606623810528326,
            "unit": "iter/sec",
            "range": "stddev: 0.0002941093950224301",
            "extra": "mean: 30.668615242437667 msec\nrounds: 33"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[periodic_1000]",
            "value": 3.1590458106681982,
            "unit": "iter/sec",
            "range": "stddev: 0.02148971913761872",
            "extra": "mean: 316.5512815999591 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[ethanol_100]",
            "value": 4.301874433118806,
            "unit": "iter/sec",
            "range": "stddev: 0.004317699389381585",
            "extra": "mean: 232.45680820000416 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[ethanol_1000]",
            "value": 0.4112798318019542,
            "unit": "iter/sec",
            "range": "stddev: 0.051437374049765734",
            "extra": "mean: 2.4314345676000357 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[periodic_100]",
            "value": 4.354400899108846,
            "unit": "iter/sec",
            "range": "stddev: 0.006163193859196625",
            "extra": "mean: 229.6527175999472 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[periodic_1000]",
            "value": 0.4134305963473195,
            "unit": "iter/sec",
            "range": "stddev: 0.049543103661612686",
            "extra": "mean: 2.4187856652000392 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[ethanol_100]",
            "value": 170.12098242953402,
            "unit": "iter/sec",
            "range": "stddev: 0.0006366052252440361",
            "extra": "mean: 5.878169675008849 msec\nrounds: 160"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[ethanol_1000]",
            "value": 166.81548116018,
            "unit": "iter/sec",
            "range": "stddev: 0.0007589181939980597",
            "extra": "mean: 5.994647457448972 msec\nrounds: 188"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[periodic_100]",
            "value": 152.58412667261743,
            "unit": "iter/sec",
            "range": "stddev: 0.0006560515169243375",
            "extra": "mean: 6.553761664511717 msec\nrounds: 155"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[periodic_1000]",
            "value": 145.77656997099268,
            "unit": "iter/sec",
            "range": "stddev: 0.000805892573297767",
            "extra": "mean: 6.859812932894393 msec\nrounds: 149"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[ethanol_100]",
            "value": 1.7994465428590107,
            "unit": "iter/sec",
            "range": "stddev: 0.006692663718895871",
            "extra": "mean: 555.7264282000688 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[ethanol_1000]",
            "value": 1.8026378022035219,
            "unit": "iter/sec",
            "range": "stddev: 0.002649740493754039",
            "extra": "mean: 554.7426103999442 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[periodic_100]",
            "value": 1.9749837045873655,
            "unit": "iter/sec",
            "range": "stddev: 0.03607337847493791",
            "extra": "mean: 506.3332915999581 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[periodic_1000]",
            "value": 2.045317913476276,
            "unit": "iter/sec",
            "range": "stddev: 0.004607071422780316",
            "extra": "mean: 488.9215478000551 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[ethanol_100]",
            "value": 17.4028704468469,
            "unit": "iter/sec",
            "range": "stddev: 0.0007927582190449985",
            "extra": "mean: 57.46178500002467 msec\nrounds: 18"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[ethanol_1000]",
            "value": 17.48036416853835,
            "unit": "iter/sec",
            "range": "stddev: 0.0007960971019268802",
            "extra": "mean: 57.20704616668274 msec\nrounds: 18"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[periodic_100]",
            "value": 20.257154713854284,
            "unit": "iter/sec",
            "range": "stddev: 0.0007438026730047952",
            "extra": "mean: 49.36527435000926 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[periodic_1000]",
            "value": 20.287896573019655,
            "unit": "iter/sec",
            "range": "stddev: 0.0008649591812257337",
            "extra": "mean: 49.29047209999453 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[ethanol_100]",
            "value": 33.84399996942158,
            "unit": "iter/sec",
            "range": "stddev: 0.0010102224075086077",
            "extra": "mean: 29.547334857094636 msec\nrounds: 21"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[ethanol_1000]",
            "value": 32.238697562047655,
            "unit": "iter/sec",
            "range": "stddev: 0.002871059177300862",
            "extra": "mean: 31.018622823560637 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[periodic_100]",
            "value": 32.59976180083473,
            "unit": "iter/sec",
            "range": "stddev: 0.0021152188269398884",
            "extra": "mean: 30.675070760007657 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[periodic_1000]",
            "value": 34.09225702261609,
            "unit": "iter/sec",
            "range": "stddev: 0.0016692751469720812",
            "extra": "mean: 29.332173558841266 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[ethanol_100]",
            "value": 151.4322713930375,
            "unit": "iter/sec",
            "range": "stddev: 0.00050624383469695",
            "extra": "mean: 6.6036122340431165 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[ethanol_1000]",
            "value": 154.737467500633,
            "unit": "iter/sec",
            "range": "stddev: 0.0003527324941490726",
            "extra": "mean: 6.4625589144782225 msec\nrounds: 152"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[periodic_100]",
            "value": 159.02829840352274,
            "unit": "iter/sec",
            "range": "stddev: 0.0003258125178164419",
            "extra": "mean: 6.288189020689718 msec\nrounds: 145"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[periodic_1000]",
            "value": 156.73261665460035,
            "unit": "iter/sec",
            "range": "stddev: 0.000324647998674952",
            "extra": "mean: 6.380292892089914 msec\nrounds: 139"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[ethanol_100]",
            "value": 81.9521893686615,
            "unit": "iter/sec",
            "range": "stddev: 0.0005269510835911",
            "extra": "mean: 12.202236544303963 msec\nrounds: 79"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[ethanol_1000]",
            "value": 80.10841227881721,
            "unit": "iter/sec",
            "range": "stddev: 0.0009238877686656253",
            "extra": "mean: 12.483083505880774 msec\nrounds: 85"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[periodic_100]",
            "value": 70.50845266913696,
            "unit": "iter/sec",
            "range": "stddev: 0.00048595729967104354",
            "extra": "mean: 14.182696714286587 msec\nrounds: 70"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[periodic_1000]",
            "value": 70.66835834106405,
            "unit": "iter/sec",
            "range": "stddev: 0.0008102814188380334",
            "extra": "mean: 14.15060464789259 msec\nrounds: 71"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[ethanol_100]",
            "value": 9.90033037432244,
            "unit": "iter/sec",
            "range": "stddev: 0.008875987168220686",
            "extra": "mean: 101.00673029999143 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[ethanol_1000]",
            "value": 10.505337605411281,
            "unit": "iter/sec",
            "range": "stddev: 0.0009097147691023877",
            "extra": "mean: 95.1897061818272 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[periodic_100]",
            "value": 12.348771388630379,
            "unit": "iter/sec",
            "range": "stddev: 0.0012465547623221641",
            "extra": "mean: 80.9797159999827 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[periodic_1000]",
            "value": 12.355364914426438,
            "unit": "iter/sec",
            "range": "stddev: 0.0012803468207016593",
            "extra": "mean: 80.93650061540266 msec\nrounds: 13"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[ethanol_100]",
            "value": 373.75746915035194,
            "unit": "iter/sec",
            "range": "stddev: 0.00008366349085378235",
            "extra": "mean: 2.675531815519996 msec\nrounds: 309"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[ethanol_1000]",
            "value": 372.8663623394493,
            "unit": "iter/sec",
            "range": "stddev: 0.00007156326600307978",
            "extra": "mean: 2.6819260223039967 msec\nrounds: 314"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[periodic_100]",
            "value": 270.5572924177464,
            "unit": "iter/sec",
            "range": "stddev: 0.00009268715107201718",
            "extra": "mean: 3.696074835255145 msec\nrounds: 261"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[periodic_1000]",
            "value": 267.3742247494087,
            "unit": "iter/sec",
            "range": "stddev: 0.00024512307034011826",
            "extra": "mean: 3.740076295451555 msec\nrounds: 264"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[ethanol_100]",
            "value": 31.45273722661805,
            "unit": "iter/sec",
            "range": "stddev: 0.003960636583533008",
            "extra": "mean: 31.793735241386642 msec\nrounds: 29"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[ethanol_1000]",
            "value": 31.576128461491457,
            "unit": "iter/sec",
            "range": "stddev: 0.0015193763073718968",
            "extra": "mean: 31.669493656245606 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[periodic_100]",
            "value": 28.448991399863655,
            "unit": "iter/sec",
            "range": "stddev: 0.005137304768856517",
            "extra": "mean: 35.15063103449047 msec\nrounds: 29"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[periodic_1000]",
            "value": 32.37851350421808,
            "unit": "iter/sec",
            "range": "stddev: 0.001376562034666645",
            "extra": "mean: 30.884679121224206 msec\nrounds: 33"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_encode_current",
            "value": 44257.083893238145,
            "unit": "iter/sec",
            "range": "stddev: 0.0000030559804105579223",
            "extra": "mean: 22.595252828051464 usec\nrounds: 9540"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_atoms_to_dict_new",
            "value": 227705.98765770692,
            "unit": "iter/sec",
            "range": "stddev: 9.542572872937424e-7",
            "extra": "mean: 4.391628038798979 usec\nrounds: 29374"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_decode_current",
            "value": 45398.16608051702,
            "unit": "iter/sec",
            "range": "stddev: 0.00002912973389871207",
            "extra": "mean: 22.027321505155648 usec\nrounds: 14572"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_dict_to_atoms_new",
            "value": 154923.89042375708,
            "unit": "iter/sec",
            "range": "stddev: 0.000020697635841949434",
            "extra": "mean: 6.454782391952205 usec\nrounds: 47126"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_read_current_aseio",
            "value": 20.649857101586612,
            "unit": "iter/sec",
            "range": "stddev: 0.05167773636859438",
            "extra": "mean: 48.42648523331263 msec\nrounds: 30"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_read_new_aseio",
            "value": 19.35333180408663,
            "unit": "iter/sec",
            "range": "stddev: 0.06075633869168511",
            "extra": "mean: 51.67068958063546 msec\nrounds: 31"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_write_current_aseio",
            "value": 25.208830201480517,
            "unit": "iter/sec",
            "range": "stddev: 0.0010961425220570261",
            "extra": "mean: 39.668639599995004 msec\nrounds: 25"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_write_new_aseio",
            "value": 25.50661900270892,
            "unit": "iter/sec",
            "range": "stddev: 0.0006397797230201974",
            "extra": "mean: 39.2055097499906 msec\nrounds: 24"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_random_access_current",
            "value": 19.08230688778942,
            "unit": "iter/sec",
            "range": "stddev: 0.06297299475894394",
            "extra": "mean: 52.404565437520034 msec\nrounds: 32"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_random_access_new",
            "value": 21.76918042213727,
            "unit": "iter/sec",
            "range": "stddev: 0.049656435287526786",
            "extra": "mean: 45.936502000005994 msec\nrounds: 29"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_via_view",
            "value": 114.17514493387995,
            "unit": "iter/sec",
            "range": "stddev: 0.002357191437279139",
            "extra": "mean: 8.758473664115868 msec\nrounds: 131"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_manual_loop",
            "value": 33.89131103996901,
            "unit": "iter/sec",
            "range": "stddev: 0.00047854487537586784",
            "extra": "mean: 29.506087823533026 msec\nrounds: 34"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_selective_keys",
            "value": 887.6584939460038,
            "unit": "iter/sec",
            "range": "stddev: 0.000031381869769047336",
            "extra": "mean: 1.1265593770804723 msec\nrounds: 602"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_row_view_iteration",
            "value": 28.849810374688634,
            "unit": "iter/sec",
            "range": "stddev: 0.02928522500706601",
            "extra": "mean: 34.66227288888351 msec\nrounds: 36"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_direct_iteration",
            "value": 23.06837548560398,
            "unit": "iter/sec",
            "range": "stddev: 0.04513585720796689",
            "extra": "mean: 43.34938975759514 msec\nrounds: 33"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_multi_column_view",
            "value": 72.66785636498585,
            "unit": "iter/sec",
            "range": "stddev: 0.020558882211442975",
            "extra": "mean: 13.761242590910362 msec\nrounds: 88"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_multi_column_manual",
            "value": 35.77991833687353,
            "unit": "iter/sec",
            "range": "stddev: 0.0010126784413391156",
            "extra": "mean: 27.948638411771753 msec\nrounds: 34"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[ethanol_100]",
            "value": 209.63697084144565,
            "unit": "iter/sec",
            "range": "stddev: 0.00016837498923207004",
            "extra": "mean: 4.7701509709197625 msec\nrounds: 172"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[ethanol_1000]",
            "value": 21.192274880206877,
            "unit": "iter/sec",
            "range": "stddev: 0.03604407280838608",
            "extra": "mean: 47.18700590911918 msec\nrounds: 22"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[periodic_100]",
            "value": 218.59022804926178,
            "unit": "iter/sec",
            "range": "stddev: 0.0001466464135981058",
            "extra": "mean: 4.574769919607928 msec\nrounds: 199"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[periodic_1000]",
            "value": 26.17057961720213,
            "unit": "iter/sec",
            "range": "stddev: 0.0005516426751801046",
            "extra": "mean: 38.21084647826035 msec\nrounds: 23"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[ethanol_100]",
            "value": 10.230200425687695,
            "unit": "iter/sec",
            "range": "stddev: 0.0011616212316150616",
            "extra": "mean: 97.74979554545511 msec\nrounds: 11"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[ethanol_1000]",
            "value": 1.7364533111916207,
            "unit": "iter/sec",
            "range": "stddev: 0.02487378400865509",
            "extra": "mean: 575.8864886000083 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[periodic_100]",
            "value": 6.210239264708882,
            "unit": "iter/sec",
            "range": "stddev: 0.0014693335237823796",
            "extra": "mean: 161.02439171429847 msec\nrounds: 7"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[periodic_1000]",
            "value": 0.7496494818938243,
            "unit": "iter/sec",
            "range": "stddev: 0.10937461074636168",
            "extra": "mean: 1.3339567680000528 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[ethanol_100]",
            "value": 25.362797109436105,
            "unit": "iter/sec",
            "range": "stddev: 0.0006983181803489825",
            "extra": "mean: 39.427827919971605 msec\nrounds: 25"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[ethanol_1000]",
            "value": 3.047909164913725,
            "unit": "iter/sec",
            "range": "stddev: 0.0013237281219787445",
            "extra": "mean: 328.0937672000164 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[periodic_100]",
            "value": 42.24453502563615,
            "unit": "iter/sec",
            "range": "stddev: 0.0001276831579854246",
            "extra": "mean: 23.671700952398908 msec\nrounds: 42"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[periodic_1000]",
            "value": 5.420469182260478,
            "unit": "iter/sec",
            "range": "stddev: 0.0009358091878011048",
            "extra": "mean: 184.48587500002608 msec\nrounds: 6"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[ethanol_100]",
            "value": 9.736333605882006,
            "unit": "iter/sec",
            "range": "stddev: 0.0018743739162833046",
            "extra": "mean: 102.70806655555337 msec\nrounds: 9"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[ethanol_1000]",
            "value": 0.9219310895902566,
            "unit": "iter/sec",
            "range": "stddev: 0.02944013116861462",
            "extra": "mean: 1.084679767600028 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[periodic_100]",
            "value": 7.279387455634836,
            "unit": "iter/sec",
            "range": "stddev: 0.0035848148490343888",
            "extra": "mean: 137.37419612496637 msec\nrounds: 8"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[periodic_1000]",
            "value": 0.7023939780347486,
            "unit": "iter/sec",
            "range": "stddev: 0.03878007359045026",
            "extra": "mean: 1.4237024110000676 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[ethanol_100]",
            "value": 55.12415346825172,
            "unit": "iter/sec",
            "range": "stddev: 0.000119781378656865",
            "extra": "mean: 18.140868150944783 msec\nrounds: 53"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[ethanol_1000]",
            "value": 19.28694597473384,
            "unit": "iter/sec",
            "range": "stddev: 0.0015047136997679005",
            "extra": "mean: 51.84854052632354 msec\nrounds: 19"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[periodic_100]",
            "value": 54.02907023317828,
            "unit": "iter/sec",
            "range": "stddev: 0.00014891262878466657",
            "extra": "mean: 18.508554666667536 msec\nrounds: 54"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[periodic_1000]",
            "value": 12.79069471258201,
            "unit": "iter/sec",
            "range": "stddev: 0.006105158670357327",
            "extra": "mean: 78.18183628574259 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[ethanol_100]",
            "value": 50.148380333646585,
            "unit": "iter/sec",
            "range": "stddev: 0.0009474847833984563",
            "extra": "mean: 19.940823479179432 msec\nrounds: 48"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[ethanol_1000]",
            "value": 5.150834067392734,
            "unit": "iter/sec",
            "range": "stddev: 0.0007534506003636706",
            "extra": "mean: 194.14331483331657 msec\nrounds: 6"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[periodic_100]",
            "value": 33.88815911179932,
            "unit": "iter/sec",
            "range": "stddev: 0.00017091555162104916",
            "extra": "mean: 29.508832176481842 msec\nrounds: 34"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[periodic_1000]",
            "value": 3.372645348442632,
            "unit": "iter/sec",
            "range": "stddev: 0.002395184085211457",
            "extra": "mean: 296.5031590000308 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[ethanol_100]",
            "value": 4.381422925580334,
            "unit": "iter/sec",
            "range": "stddev: 0.005290483072229056",
            "extra": "mean: 228.23635539989482 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[ethanol_1000]",
            "value": 0.42821226646277377,
            "unit": "iter/sec",
            "range": "stddev: 0.06250341087864274",
            "extra": "mean: 2.3352904115999538 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[periodic_100]",
            "value": 4.624269027111734,
            "unit": "iter/sec",
            "range": "stddev: 0.0044071712203682285",
            "extra": "mean: 216.25039420005123 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[periodic_1000]",
            "value": 0.43869111744084627,
            "unit": "iter/sec",
            "range": "stddev: 0.05890103507642186",
            "extra": "mean: 2.2795082011999965 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "name": "Fabian Zills",
            "username": "PythonFZ",
            "email": "46721498+PythonFZ@users.noreply.github.com"
          },
          "committer": {
            "name": "GitHub",
            "username": "web-flow",
            "email": "noreply@github.com"
          },
          "id": "79c1b63482e96c8b91022fca70c0ac54a5fb18af",
          "message": "Fix/full znh5md support (#16)\n\n* test: add RED tests for znh5md <-> asebytes full round-trip coverage\n\nParametrized tests over all s22_* fixtures verify:\n- znh5md write -> asebytes read (catches H5MD path mapping bug with\n  per-atom calc results like energies, stresses, magmoms)\n- asebytes write -> znh5md read\n- Full bidirectional round-trip\n- *.h5 extension with H5MD content (catches registry routing bug)\n\n9 tests fail RED, exposing two bugs:\n1. H5MDStore path mapping loses actual H5MD paths on round-trip\n2. Registry sends *.h5 H5MD files to RaggedColumnarBackend\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>\n\n* feat(fix-h5md): add H5MD content sniffing for *.h5 files\n\n- Add _is_h5md_file() helper that checks for \"h5md\" group in HDF5 files\n- Insert sniffing logic in resolve_backend to redirect *.h5 files\n  containing H5MD metadata to the H5MD backend\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>\n\n* fix(h5md): cache discovered H5 paths to fix round-trip with foreign properties\n\nProperties like energies, stresses, magmoms placed by znh5md in\n/particles/ were lost on read because _column_to_h5() statically\nmapped them to /observables/. Now _walk_elements() caches the actual\nH5 path during discovery, and _get_ds() checks the cache first.\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>\n\n* fix(h5md): remove redundant has_array guard in per-atom detection\n\nIn _discover(), columns from list_arrays() are known to exist, so the\nhas_array() check was redundant and broke per-atom detection for columns\nwhose _column_to_h5() mapping disagreed with the actual H5 path (e.g.\nper-atom energies placed in /particles/ by znh5md).\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>\n\n* fix(h5md): address PR #16 CodeRabbit review comments\n\n- Use H5 path (/particles/ vs /observables/) for per-atom detection\n  instead of shape heuristic that misclassified frame-level vectors\n- Centralize path resolution with _resolve_h5_path helper used by\n  both _get_ds and has_array to fix foreign column lookups\n- Remove test slicing ([:n]) that masked potential padding leaks and\n  add explicit atom count assertions\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>\n\n* test(h5md): use full assert_atoms_equal in all round-trip tests\n\nReplace weak positions/numbers-only assertions in TestAsebytesToZnH5MD\nand TestBidirectionalRoundtrip with assert_atoms_equal to catch\nregressions in cell, pbc, info, arrays, and calc properties. Merge\nTestH5ExtensionWithH5MDContent into TestZnH5MDToAsebytes as a\nparametrized extension (.h5md/.h5) to remove duplication.\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>\n\n---------\n\nCo-authored-by: Claude Opus 4.6 <noreply@anthropic.com>",
          "timestamp": "2026-03-10T21:03:01Z",
          "url": "https://github.com/zincware/asebytes/commit/79c1b63482e96c8b91022fca70c0ac54a5fb18af"
        },
        "date": 1773178042430,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 3498.5265458626636,
            "unit": "iter/sec",
            "range": "stddev: 0.000009325920812989368",
            "extra": "mean: 285.83461834314045 usec\nrounds: 2028"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 339.92845073018253,
            "unit": "iter/sec",
            "range": "stddev: 0.000024563230577757688",
            "extra": "mean: 2.9417955391846498 msec\nrounds: 319"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[periodic_100]",
            "value": 3304.7542054711794,
            "unit": "iter/sec",
            "range": "stddev: 0.000011211742561262494",
            "extra": "mean: 302.5943649135697 usec\nrounds: 2776"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 328.7946762511516,
            "unit": "iter/sec",
            "range": "stddev: 0.00008034282485718624",
            "extra": "mean: 3.041411775281132 msec\nrounds: 267"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[ethanol_100]",
            "value": 123.13486873953252,
            "unit": "iter/sec",
            "range": "stddev: 0.0006323542888614995",
            "extra": "mean: 8.121176481012071 msec\nrounds: 79"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 13.987109382083377,
            "unit": "iter/sec",
            "range": "stddev: 0.0010178053187437721",
            "extra": "mean: 71.49440050000167 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[periodic_100]",
            "value": 47.341398162094194,
            "unit": "iter/sec",
            "range": "stddev: 0.0005472588626218613",
            "extra": "mean: 21.123161520833378 msec\nrounds: 48"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_zarr[periodic_1000]",
            "value": 4.374861027617717,
            "unit": "iter/sec",
            "range": "stddev: 0.01970246584824701",
            "extra": "mean: 228.57868940000117 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[ethanol_100]",
            "value": 1811.6790547737146,
            "unit": "iter/sec",
            "range": "stddev: 0.00009550253363258824",
            "extra": "mean: 551.9741465051621 usec\nrounds: 744"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 227.89583376792015,
            "unit": "iter/sec",
            "range": "stddev: 0.00005427029532745436",
            "extra": "mean: 4.387969641508933 msec\nrounds: 159"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[periodic_100]",
            "value": 1808.2243866378076,
            "unit": "iter/sec",
            "range": "stddev: 0.000013891400144071548",
            "extra": "mean: 553.028710037137 usec\nrounds: 807"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_h5md[periodic_1000]",
            "value": 208.66299203226265,
            "unit": "iter/sec",
            "range": "stddev: 0.0002339398072686255",
            "extra": "mean: 4.7924166631588605 msec\nrounds: 95"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 901.7165321826502,
            "unit": "iter/sec",
            "range": "stddev: 0.00004853186461364443",
            "extra": "mean: 1.1089959696973168 msec\nrounds: 165"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 245.78666470638206,
            "unit": "iter/sec",
            "range": "stddev: 0.00009212657930397898",
            "extra": "mean: 4.068568981130872 msec\nrounds: 53"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[periodic_100]",
            "value": 873.7909058684779,
            "unit": "iter/sec",
            "range": "stddev: 0.00013472044234014228",
            "extra": "mean: 1.144438553072466 msec\nrounds: 179"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 243.46615333306283,
            "unit": "iter/sec",
            "range": "stddev: 0.00007815226037749931",
            "extra": "mean: 4.107347104761602 msec\nrounds: 105"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[ethanol_100]",
            "value": 337.7529304516167,
            "unit": "iter/sec",
            "range": "stddev: 0.00007708608735982827",
            "extra": "mean: 2.9607441115695976 msec\nrounds: 242"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[ethanol_1000]",
            "value": 47.01906807760346,
            "unit": "iter/sec",
            "range": "stddev: 0.0009411954415177408",
            "extra": "mean: 21.267967250000197 msec\nrounds: 40"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[periodic_100]",
            "value": 332.0680118931734,
            "unit": "iter/sec",
            "range": "stddev: 0.00008053434769441412",
            "extra": "mean: 3.011431285714148 msec\nrounds: 245"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_asebytes_redis[periodic_1000]",
            "value": 47.95736275850421,
            "unit": "iter/sec",
            "range": "stddev: 0.0003175934526022565",
            "extra": "mean: 20.85185553333354 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[ethanol_100]",
            "value": 145.59505265947772,
            "unit": "iter/sec",
            "range": "stddev: 0.00008529836816166916",
            "extra": "mean: 6.86836524822606 msec\nrounds: 141"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[ethanol_1000]",
            "value": 13.599483567771033,
            "unit": "iter/sec",
            "range": "stddev: 0.008650819915250945",
            "extra": "mean: 73.53220400000092 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[periodic_100]",
            "value": 87.93383258033492,
            "unit": "iter/sec",
            "range": "stddev: 0.00014225459346228897",
            "extra": "mean: 11.372187139533766 msec\nrounds: 86"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_aselmdb[periodic_1000]",
            "value": 8.857127317804945,
            "unit": "iter/sec",
            "range": "stddev: 0.0004344117854070735",
            "extra": "mean: 112.90342388889012 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[ethanol_100]",
            "value": 1661.675517261787,
            "unit": "iter/sec",
            "range": "stddev: 0.000016871337385560433",
            "extra": "mean: 601.8022108479173 usec\nrounds: 1309"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[ethanol_1000]",
            "value": 270.1663616148667,
            "unit": "iter/sec",
            "range": "stddev: 0.010898609105754537",
            "extra": "mean: 3.7014230566036987 msec\nrounds: 265"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[periodic_100]",
            "value": 628.0334258574833,
            "unit": "iter/sec",
            "range": "stddev: 0.0074829817047094",
            "extra": "mean: 1.5922719378107197 msec\nrounds: 804"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_znh5md[periodic_1000]",
            "value": 120.60704169260376,
            "unit": "iter/sec",
            "range": "stddev: 0.011833661199173631",
            "extra": "mean: 8.291389838984212 msec\nrounds: 118"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[ethanol_100]",
            "value": 52.426581849404904,
            "unit": "iter/sec",
            "range": "stddev: 0.001419844519435551",
            "extra": "mean: 19.074293320752727 msec\nrounds: 53"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[ethanol_1000]",
            "value": 5.472003503658267,
            "unit": "iter/sec",
            "range": "stddev: 0.004086291695965362",
            "extra": "mean: 182.74842099999708 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[periodic_100]",
            "value": 53.88604538835582,
            "unit": "iter/sec",
            "range": "stddev: 0.00012165094362763861",
            "extra": "mean: 18.557680245284597 msec\nrounds: 53"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_trajectory_sqlite[periodic_1000]",
            "value": 5.505710997855503,
            "unit": "iter/sec",
            "range": "stddev: 0.00045118000873113585",
            "extra": "mean: 181.62958433334117 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[ethanol_100]",
            "value": 380.5584839663338,
            "unit": "iter/sec",
            "range": "stddev: 0.00009296687075005678",
            "extra": "mean: 2.6277170057479657 msec\nrounds: 348"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[ethanol_1000]",
            "value": 35.02676163869932,
            "unit": "iter/sec",
            "range": "stddev: 0.0037089188875177427",
            "extra": "mean: 28.549599027023667 msec\nrounds: 37"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[periodic_100]",
            "value": 407.88076375062406,
            "unit": "iter/sec",
            "range": "stddev: 0.0001506092178773257",
            "extra": "mean: 2.451696890053374 msec\nrounds: 382"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_lmdb[periodic_1000]",
            "value": 40.72804035753133,
            "unit": "iter/sec",
            "range": "stddev: 0.00033721276660225036",
            "extra": "mean: 24.553108649998734 msec\nrounds: 40"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[ethanol_100]",
            "value": 1.3765287379557918,
            "unit": "iter/sec",
            "range": "stddev: 0.005647994201531758",
            "extra": "mean: 726.4650365999955 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[ethanol_1000]",
            "value": 0.13738306828941224,
            "unit": "iter/sec",
            "range": "stddev: 0.0819782168149196",
            "extra": "mean: 7.2789173546000026 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[periodic_100]",
            "value": 1.4355178675409006,
            "unit": "iter/sec",
            "range": "stddev: 0.041521946199046526",
            "extra": "mean: 696.6127156000084 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_zarr[periodic_1000]",
            "value": 0.143932438268233,
            "unit": "iter/sec",
            "range": "stddev: 0.033360917533001494",
            "extra": "mean: 6.947704159200003 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[ethanol_100]",
            "value": 11.399116816377163,
            "unit": "iter/sec",
            "range": "stddev: 0.005363283100162402",
            "extra": "mean: 87.72609458333609 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[ethanol_1000]",
            "value": 1.1635423027073761,
            "unit": "iter/sec",
            "range": "stddev: 0.0037303391344181702",
            "extra": "mean: 859.4444719999956 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[periodic_100]",
            "value": 15.31138020508032,
            "unit": "iter/sec",
            "range": "stddev: 0.0005185445101289776",
            "extra": "mean: 65.31089859999686 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_h5md[periodic_1000]",
            "value": 1.5119118079393419,
            "unit": "iter/sec",
            "range": "stddev: 0.014679037283841729",
            "extra": "mean: 661.4142404000063 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[ethanol_100]",
            "value": 24.598087833394906,
            "unit": "iter/sec",
            "range": "stddev: 0.0010085200596760093",
            "extra": "mean: 40.65356652001128 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.4773649911577005,
            "unit": "iter/sec",
            "range": "stddev: 0.0036397116585565625",
            "extra": "mean: 403.65469100000837 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[periodic_100]",
            "value": 25.048258939068912,
            "unit": "iter/sec",
            "range": "stddev: 0.0007517206419198516",
            "extra": "mean: 39.92293446153475 msec\nrounds: 26"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_mongodb[periodic_1000]",
            "value": 2.4918877553501266,
            "unit": "iter/sec",
            "range": "stddev: 0.004593140589361267",
            "extra": "mean: 401.3021846000015 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[ethanol_100]",
            "value": 32.751224024107565,
            "unit": "iter/sec",
            "range": "stddev: 0.0029829240922890367",
            "extra": "mean: 30.533209972974408 msec\nrounds: 37"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[ethanol_1000]",
            "value": 3.6320137966433337,
            "unit": "iter/sec",
            "range": "stddev: 0.005522741847229005",
            "extra": "mean: 275.32935059998636 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[periodic_100]",
            "value": 37.97340705361642,
            "unit": "iter/sec",
            "range": "stddev: 0.0006834855972940866",
            "extra": "mean: 26.33421853846439 msec\nrounds: 39"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_asebytes_redis[periodic_1000]",
            "value": 3.6598002063683976,
            "unit": "iter/sec",
            "range": "stddev: 0.0028236577579762263",
            "extra": "mean: 273.2389593999983 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[ethanol_100]",
            "value": 135.56048474476395,
            "unit": "iter/sec",
            "range": "stddev: 0.0007326899607616395",
            "extra": "mean: 7.37678093939263 msec\nrounds: 132"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[ethanol_1000]",
            "value": 13.827844060493415,
            "unit": "iter/sec",
            "range": "stddev: 0.0006987264269896015",
            "extra": "mean: 72.31785342857832 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[periodic_100]",
            "value": 84.47183351032457,
            "unit": "iter/sec",
            "range": "stddev: 0.0006322010332582791",
            "extra": "mean: 11.838265590361253 msec\nrounds: 83"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_aselmdb[periodic_1000]",
            "value": 8.434387313084052,
            "unit": "iter/sec",
            "range": "stddev: 0.0004509163350125315",
            "extra": "mean: 118.56225744444122 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[ethanol_100]",
            "value": 2.154253179104748,
            "unit": "iter/sec",
            "range": "stddev: 0.0029428523614754595",
            "extra": "mean: 464.19799199998124 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[ethanol_1000]",
            "value": 0.2149911343966167,
            "unit": "iter/sec",
            "range": "stddev: 0.022441392496819867",
            "extra": "mean: 4.651354590999995 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[periodic_100]",
            "value": 2.441792805592972,
            "unit": "iter/sec",
            "range": "stddev: 0.0007753755995144199",
            "extra": "mean: 409.5351570000048 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_znh5md[periodic_1000]",
            "value": 0.24108999754260274,
            "unit": "iter/sec",
            "range": "stddev: 0.037411693134317726",
            "extra": "mean: 4.147828654000011 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[ethanol_100]",
            "value": 24.860434564489726,
            "unit": "iter/sec",
            "range": "stddev: 0.0005118036872812463",
            "extra": "mean: 40.2245583200056 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[ethanol_1000]",
            "value": 2.497413774445676,
            "unit": "iter/sec",
            "range": "stddev: 0.0009562009580598324",
            "extra": "mean: 400.4142245999901 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[periodic_100]",
            "value": 24.83507103828741,
            "unit": "iter/sec",
            "range": "stddev: 0.0004440393040139855",
            "extra": "mean: 40.265638799999124 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_read_positions_single_sqlite[periodic_1000]",
            "value": 2.5057073486033947,
            "unit": "iter/sec",
            "range": "stddev: 0.0010482523209252804",
            "extra": "mean: 399.0889041999935 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[ethanol_100]",
            "value": 8209.320679862605,
            "unit": "iter/sec",
            "range": "stddev: 0.00003986126841687597",
            "extra": "mean: 121.81275881364844 usec\nrounds: 3035"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[ethanol_1000]",
            "value": 834.2511570145749,
            "unit": "iter/sec",
            "range": "stddev: 0.000017419080324496204",
            "extra": "mean: 1.1986797879652558 msec\nrounds: 698"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[periodic_100]",
            "value": 9028.184184341453,
            "unit": "iter/sec",
            "range": "stddev: 0.000008194476748738086",
            "extra": "mean: 110.76424445730817 usec\nrounds: 5367"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_lmdb[periodic_1000]",
            "value": 848.0862291644037,
            "unit": "iter/sec",
            "range": "stddev: 0.000019652356339512924",
            "extra": "mean: 1.1791253832588142 msec\nrounds: 681"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[ethanol_100]",
            "value": 695.3055488810829,
            "unit": "iter/sec",
            "range": "stddev: 0.00019119484246099533",
            "extra": "mean: 1.4382166252077884 msec\nrounds: 603"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[ethanol_1000]",
            "value": 97.63009269688557,
            "unit": "iter/sec",
            "range": "stddev: 0.0002931539100675718",
            "extra": "mean: 10.242743526882878 msec\nrounds: 93"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[periodic_100]",
            "value": 700.4726491204341,
            "unit": "iter/sec",
            "range": "stddev: 0.00008237563771602782",
            "extra": "mean: 1.4276074893940183 msec\nrounds: 660"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_zarr[periodic_1000]",
            "value": 97.08619824225153,
            "unit": "iter/sec",
            "range": "stddev: 0.00033741176521911607",
            "extra": "mean: 10.300125230002095 msec\nrounds: 100"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[ethanol_100]",
            "value": 3303.1922580382866,
            "unit": "iter/sec",
            "range": "stddev: 0.000012628671138544834",
            "extra": "mean: 302.7374496796272 usec\nrounds: 2186"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[ethanol_1000]",
            "value": 436.31540865303793,
            "unit": "iter/sec",
            "range": "stddev: 0.00038720279671978526",
            "extra": "mean: 2.2919199738719502 msec\nrounds: 421"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[periodic_100]",
            "value": 3301.2210644469446,
            "unit": "iter/sec",
            "range": "stddev: 0.000012983017051031877",
            "extra": "mean: 302.9182173740705 usec\nrounds: 2567"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_h5md[periodic_1000]",
            "value": 468.22501119359526,
            "unit": "iter/sec",
            "range": "stddev: 0.00008000001146544305",
            "extra": "mean: 2.135725294662941 msec\nrounds: 431"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[ethanol_100]",
            "value": 912.693753210816,
            "unit": "iter/sec",
            "range": "stddev: 0.000025152060454869757",
            "extra": "mean: 1.0956577674406607 msec\nrounds: 172"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[ethanol_1000]",
            "value": 245.7214086954024,
            "unit": "iter/sec",
            "range": "stddev: 0.00009037043580782866",
            "extra": "mean: 4.0696494672940995 msec\nrounds: 107"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[periodic_100]",
            "value": 911.4545269224105,
            "unit": "iter/sec",
            "range": "stddev: 0.000051663264074142724",
            "extra": "mean: 1.0971474390242697 msec\nrounds: 164"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_mongodb[periodic_1000]",
            "value": 182.00196081407606,
            "unit": "iter/sec",
            "range": "stddev: 0.013185588359197148",
            "extra": "mean: 5.494446298968993 msec\nrounds: 97"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[ethanol_100]",
            "value": 364.87599958653163,
            "unit": "iter/sec",
            "range": "stddev: 0.00007657201939607437",
            "extra": "mean: 2.7406571030519267 msec\nrounds: 262"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[ethanol_1000]",
            "value": 54.19318118862859,
            "unit": "iter/sec",
            "range": "stddev: 0.00023595789202955677",
            "extra": "mean: 18.45250598076776 msec\nrounds: 52"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[periodic_100]",
            "value": 364.5122183465686,
            "unit": "iter/sec",
            "range": "stddev: 0.00006950659738566166",
            "extra": "mean: 2.743392264149638 msec\nrounds: 265"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_asebytes_redis[periodic_1000]",
            "value": 53.76854340448814,
            "unit": "iter/sec",
            "range": "stddev: 0.0005115468519038091",
            "extra": "mean: 18.598234891305026 msec\nrounds: 46"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[ethanol_100]",
            "value": 148.2467067656337,
            "unit": "iter/sec",
            "range": "stddev: 0.0000827130071798338",
            "extra": "mean: 6.74551240845384 msec\nrounds: 142"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[ethanol_1000]",
            "value": 13.387507148359758,
            "unit": "iter/sec",
            "range": "stddev: 0.01182288390989866",
            "extra": "mean: 74.69650540000052 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[periodic_100]",
            "value": 88.31537269350711,
            "unit": "iter/sec",
            "range": "stddev: 0.00022289345574514444",
            "extra": "mean: 11.323057011494889 msec\nrounds: 87"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_aselmdb[periodic_1000]",
            "value": 8.768788350582224,
            "unit": "iter/sec",
            "range": "stddev: 0.0032328956073534648",
            "extra": "mean: 114.04084122222002 msec\nrounds: 9"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[ethanol_100]",
            "value": 2584.3454450301015,
            "unit": "iter/sec",
            "range": "stddev: 0.000020658773953825563",
            "extra": "mean: 386.94517481131567 usec\nrounds: 2128"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[ethanol_1000]",
            "value": 2065.4881944163617,
            "unit": "iter/sec",
            "range": "stddev: 0.000014456731403887598",
            "extra": "mean: 484.14704218755736 usec\nrounds: 1683"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[periodic_100]",
            "value": 2592.7060138578518,
            "unit": "iter/sec",
            "range": "stddev: 0.000018319490728606586",
            "extra": "mean: 385.6974121458671 usec\nrounds: 2157"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_znh5md[periodic_1000]",
            "value": 2066.3657075304586,
            "unit": "iter/sec",
            "range": "stddev: 0.000015932472381664434",
            "extra": "mean: 483.9414419024178 usec\nrounds: 1661"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[ethanol_100]",
            "value": 62.70099775203061,
            "unit": "iter/sec",
            "range": "stddev: 0.0002688943507640342",
            "extra": "mean: 15.948709523806812 msec\nrounds: 63"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[ethanol_1000]",
            "value": 6.357649203550191,
            "unit": "iter/sec",
            "range": "stddev: 0.003197097775084654",
            "extra": "mean: 157.2908425714315 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[periodic_100]",
            "value": 62.238918911008156,
            "unit": "iter/sec",
            "range": "stddev: 0.0010068480807231281",
            "extra": "mean: 16.067117126983558 msec\nrounds: 63"
          },
          {
            "name": "tests/benchmarks/test_bench_property_access.py::test_column_energy_sqlite[periodic_1000]",
            "value": 6.390626080672361,
            "unit": "iter/sec",
            "range": "stddev: 0.0012688261226441705",
            "extra": "mean: 156.479191142848 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 244.0389615367495,
            "unit": "iter/sec",
            "range": "stddev: 0.0011536676243051808",
            "extra": "mean: 4.097706340425528 msec\nrounds: 235"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 25.10966783437163,
            "unit": "iter/sec",
            "range": "stddev: 0.0011163204422112273",
            "extra": "mean: 39.82529783333651 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[periodic_100]",
            "value": 284.86795347967467,
            "unit": "iter/sec",
            "range": "stddev: 0.0003295852856234299",
            "extra": "mean: 3.5103983715435723 msec\nrounds: 253"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 22.187417665361078,
            "unit": "iter/sec",
            "range": "stddev: 0.026936779216358682",
            "extra": "mean: 45.070589785723314 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[ethanol_100]",
            "value": 24.14367356228202,
            "unit": "iter/sec",
            "range": "stddev: 0.003374930531990796",
            "extra": "mean: 41.418717720000586 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 2.759978024767845,
            "unit": "iter/sec",
            "range": "stddev: 0.0030719799038280518",
            "extra": "mean: 362.321725400011 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[periodic_100]",
            "value": 10.953373973410367,
            "unit": "iter/sec",
            "range": "stddev: 0.0020244312316776945",
            "extra": "mean: 91.29607027273323 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_zarr[periodic_1000]",
            "value": 1.1213281408077729,
            "unit": "iter/sec",
            "range": "stddev: 0.03569885394706892",
            "extra": "mean: 891.7996112000083 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[ethanol_100]",
            "value": 208.79603035000665,
            "unit": "iter/sec",
            "range": "stddev: 0.00029713507140307743",
            "extra": "mean: 4.789363084746827 msec\nrounds: 177"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 21.491042773042977,
            "unit": "iter/sec",
            "range": "stddev: 0.02832906659558092",
            "extra": "mean: 46.53101343478491 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[periodic_100]",
            "value": 232.41515466876515,
            "unit": "iter/sec",
            "range": "stddev: 0.0007309844946232901",
            "extra": "mean: 4.3026454166690895 msec\nrounds: 168"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_h5md[periodic_1000]",
            "value": 27.351263055411323,
            "unit": "iter/sec",
            "range": "stddev: 0.002853909915460002",
            "extra": "mean: 36.56138285000168 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 210.45692086044286,
            "unit": "iter/sec",
            "range": "stddev: 0.011105567461165476",
            "extra": "mean: 4.751566239359336 msec\nrounds: 188"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 23.026092932494095,
            "unit": "iter/sec",
            "range": "stddev: 0.032784356560080725",
            "extra": "mean: 43.42899174999916 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[periodic_100]",
            "value": 254.06086116840171,
            "unit": "iter/sec",
            "range": "stddev: 0.0010418689129504163",
            "extra": "mean: 3.936064750001614 msec\nrounds: 260"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 27.671438489397975,
            "unit": "iter/sec",
            "range": "stddev: 0.0035436834491133743",
            "extra": "mean: 36.13834533333494 msec\nrounds: 21"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[ethanol_100]",
            "value": 136.1808198030134,
            "unit": "iter/sec",
            "range": "stddev: 0.0005410349886075811",
            "extra": "mean: 7.343178000004021 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[ethanol_1000]",
            "value": 13.40444097350928,
            "unit": "iter/sec",
            "range": "stddev: 0.03580831786577074",
            "extra": "mean: 74.6021413333286 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[periodic_100]",
            "value": 148.59041201319923,
            "unit": "iter/sec",
            "range": "stddev: 0.00042898945070165087",
            "extra": "mean: 6.729909328948966 msec\nrounds: 152"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_asebytes_redis[periodic_1000]",
            "value": 14.097470957412845,
            "unit": "iter/sec",
            "range": "stddev: 0.037663467782227594",
            "extra": "mean: 70.93470899999777 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[ethanol_100]",
            "value": 59.166700057794344,
            "unit": "iter/sec",
            "range": "stddev: 0.0007513952901978623",
            "extra": "mean: 16.901398912279962 msec\nrounds: 57"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[ethanol_1000]",
            "value": 5.868774886063128,
            "unit": "iter/sec",
            "range": "stddev: 0.002835464907008529",
            "extra": "mean: 170.39331366666488 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[periodic_100]",
            "value": 44.576836989902304,
            "unit": "iter/sec",
            "range": "stddev: 0.001236971462951444",
            "extra": "mean: 22.433175333335637 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_aselmdb[periodic_1000]",
            "value": 3.891964671378792,
            "unit": "iter/sec",
            "range": "stddev: 0.07444741446660527",
            "extra": "mean: 256.9396396000002 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[ethanol_100]",
            "value": 2.178242404433873,
            "unit": "iter/sec",
            "range": "stddev: 0.0011978493070112241",
            "extra": "mean: 459.0857280000023 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[ethanol_1000]",
            "value": 0.21551023545738987,
            "unit": "iter/sec",
            "range": "stddev: 0.03613125704955265",
            "extra": "mean: 4.640150839599994 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[periodic_100]",
            "value": 2.4237558210350834,
            "unit": "iter/sec",
            "range": "stddev: 0.0022445444047873263",
            "extra": "mean: 412.58281519998263 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_znh5md[periodic_1000]",
            "value": 0.24139727426927338,
            "unit": "iter/sec",
            "range": "stddev: 0.042257568929719776",
            "extra": "mean: 4.142548846199986 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[ethanol_100]",
            "value": 17.89524291225101,
            "unit": "iter/sec",
            "range": "stddev: 0.0040401332018471445",
            "extra": "mean: 55.88077261110572 msec\nrounds: 18"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[ethanol_1000]",
            "value": 1.714860252049393,
            "unit": "iter/sec",
            "range": "stddev: 0.08482652785836592",
            "extra": "mean: 583.1378963999668 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[periodic_100]",
            "value": 18.174411926341882,
            "unit": "iter/sec",
            "range": "stddev: 0.0014414161876355645",
            "extra": "mean: 55.02241305263947 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_trajectory_sqlite[periodic_1000]",
            "value": 1.764475932943279,
            "unit": "iter/sec",
            "range": "stddev: 0.013414750504863385",
            "extra": "mean: 566.7405155999631 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[ethanol_100]",
            "value": 210.04750586690434,
            "unit": "iter/sec",
            "range": "stddev: 0.0008676238194675354",
            "extra": "mean: 4.760827774996983 msec\nrounds: 200"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[ethanol_1000]",
            "value": 15.711760946530266,
            "unit": "iter/sec",
            "range": "stddev: 0.052450605707914245",
            "extra": "mean: 63.64658954544728 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[periodic_100]",
            "value": 241.8061192082905,
            "unit": "iter/sec",
            "range": "stddev: 0.0004831110831632494",
            "extra": "mean: 4.135544639127207 msec\nrounds: 230"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_lmdb[periodic_1000]",
            "value": 22.622514269117058,
            "unit": "iter/sec",
            "range": "stddev: 0.0037105040408080985",
            "extra": "mean: 44.20375154167289 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[ethanol_100]",
            "value": 1.344468330471973,
            "unit": "iter/sec",
            "range": "stddev: 0.030015911257852478",
            "extra": "mean: 743.7884383999972 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[ethanol_1000]",
            "value": 0.13838936460453177,
            "unit": "iter/sec",
            "range": "stddev: 0.0801509812031343",
            "extra": "mean: 7.225988809599994 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[periodic_100]",
            "value": 1.3882028120663763,
            "unit": "iter/sec",
            "range": "stddev: 0.023156425329290097",
            "extra": "mean: 720.3558379999777 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_zarr[periodic_1000]",
            "value": 0.14614084937776245,
            "unit": "iter/sec",
            "range": "stddev: 0.06515768220802948",
            "extra": "mean: 6.842713753599992 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[ethanol_100]",
            "value": 11.439366911649342,
            "unit": "iter/sec",
            "range": "stddev: 0.0015741511370597453",
            "extra": "mean: 87.41742508334482 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[ethanol_1000]",
            "value": 1.1306927404629428,
            "unit": "iter/sec",
            "range": "stddev: 0.002760517452607248",
            "extra": "mean: 884.413567200022 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[periodic_100]",
            "value": 14.117606395372725,
            "unit": "iter/sec",
            "range": "stddev: 0.006014696003505549",
            "extra": "mean: 70.8335373571377 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_h5md[periodic_1000]",
            "value": 1.467757696952579,
            "unit": "iter/sec",
            "range": "stddev: 0.00434149075685862",
            "extra": "mean: 681.3113649999877 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[ethanol_100]",
            "value": 22.414542920324745,
            "unit": "iter/sec",
            "range": "stddev: 0.0016740682736228712",
            "extra": "mean: 44.61389213041832 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.0678077297320843,
            "unit": "iter/sec",
            "range": "stddev: 0.08322217028243595",
            "extra": "mean: 483.60395679997055 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[periodic_100]",
            "value": 22.165911422346525,
            "unit": "iter/sec",
            "range": "stddev: 0.0028131944093846787",
            "extra": "mean: 45.114319052626534 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_mongodb[periodic_1000]",
            "value": 2.273374301920764,
            "unit": "iter/sec",
            "range": "stddev: 0.004261817333257853",
            "extra": "mean: 439.87477079999735 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[ethanol_100]",
            "value": 31.500237113256095,
            "unit": "iter/sec",
            "range": "stddev: 0.001880056162985108",
            "extra": "mean: 31.74579278259384 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[ethanol_1000]",
            "value": 3.073269279369656,
            "unit": "iter/sec",
            "range": "stddev: 0.004659418319416333",
            "extra": "mean: 325.386391200027 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[periodic_100]",
            "value": 31.77864553793093,
            "unit": "iter/sec",
            "range": "stddev: 0.0019050743862203995",
            "extra": "mean: 31.46767217647467 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_asebytes_redis[periodic_1000]",
            "value": 3.0534474252576302,
            "unit": "iter/sec",
            "range": "stddev: 0.02048344972534969",
            "extra": "mean: 327.49867960003485 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[ethanol_100]",
            "value": 59.00743995200123,
            "unit": "iter/sec",
            "range": "stddev: 0.0011510609026313633",
            "extra": "mean: 16.94701550878052 msec\nrounds: 57"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[ethanol_1000]",
            "value": 5.849741711616059,
            "unit": "iter/sec",
            "range": "stddev: 0.002102812391100748",
            "extra": "mean: 170.94771859999582 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[periodic_100]",
            "value": 44.85406791799316,
            "unit": "iter/sec",
            "range": "stddev: 0.0009539848710635301",
            "extra": "mean: 22.294521911107445 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_aselmdb[periodic_1000]",
            "value": 4.493294083893928,
            "unit": "iter/sec",
            "range": "stddev: 0.0024656717350913008",
            "extra": "mean: 222.55387280001742 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[ethanol_100]",
            "value": 2.1453033424622383,
            "unit": "iter/sec",
            "range": "stddev: 0.010825584343531163",
            "extra": "mean: 466.13454620000994 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[ethanol_1000]",
            "value": 0.21561356430421696,
            "unit": "iter/sec",
            "range": "stddev: 0.08702943742726162",
            "extra": "mean: 4.6379271324 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[periodic_100]",
            "value": 2.4614425934235675,
            "unit": "iter/sec",
            "range": "stddev: 0.0023098138865718766",
            "extra": "mean: 406.2658226000394 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_znh5md[periodic_1000]",
            "value": 0.24144269496510407,
            "unit": "iter/sec",
            "range": "stddev: 0.024643098848431723",
            "extra": "mean: 4.141769541400004 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[ethanol_100]",
            "value": 18.439602555060784,
            "unit": "iter/sec",
            "range": "stddev: 0.0010243725489378715",
            "extra": "mean: 54.23110378946579 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[ethanol_1000]",
            "value": 1.8439391619739471,
            "unit": "iter/sec",
            "range": "stddev: 0.0038479881965928224",
            "extra": "mean: 542.3172416000398 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[periodic_100]",
            "value": 17.8338348538906,
            "unit": "iter/sec",
            "range": "stddev: 0.0045488222499957",
            "extra": "mean: 56.073189428567666 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_random_access.py::test_random_single_sqlite[periodic_1000]",
            "value": 1.708853142421276,
            "unit": "iter/sec",
            "range": "stddev: 0.08430879219423626",
            "extra": "mean: 585.1877936000392 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 234.96320640671604,
            "unit": "iter/sec",
            "range": "stddev: 0.0013254773141495883",
            "extra": "mean: 4.255985502125905 msec\nrounds: 235"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 18.088685198547978,
            "unit": "iter/sec",
            "range": "stddev: 0.04691105954201764",
            "extra": "mean: 55.28317780002453 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[periodic_100]",
            "value": 224.2825568658728,
            "unit": "iter/sec",
            "range": "stddev: 0.009444014100547484",
            "extra": "mean: 4.4586614936712525 msec\nrounds: 237"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 26.499443292599675,
            "unit": "iter/sec",
            "range": "stddev: 0.0025155419905098226",
            "extra": "mean: 37.73664182142511 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[ethanol_100]",
            "value": 23.59211465776357,
            "unit": "iter/sec",
            "range": "stddev: 0.001076937637434908",
            "extra": "mean: 42.3870439130358 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 2.707183061402466,
            "unit": "iter/sec",
            "range": "stddev: 0.0017835905503194459",
            "extra": "mean: 369.38765400000193 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[periodic_100]",
            "value": 10.8220155055448,
            "unit": "iter/sec",
            "range": "stddev: 0.0014254358718760669",
            "extra": "mean: 92.40422909093385 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_zarr[periodic_1000]",
            "value": 1.0838664514732155,
            "unit": "iter/sec",
            "range": "stddev: 0.06454183522256361",
            "extra": "mean: 922.622892000004 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[ethanol_100]",
            "value": 192.91361972190396,
            "unit": "iter/sec",
            "range": "stddev: 0.0004605741777669999",
            "extra": "mean: 5.18366718452309 msec\nrounds: 168"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 20.41457274677596,
            "unit": "iter/sec",
            "range": "stddev: 0.03046109003801432",
            "extra": "mean: 48.984615666665285 msec\nrounds: 21"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[periodic_100]",
            "value": 186.35846816411672,
            "unit": "iter/sec",
            "range": "stddev: 0.011896551416806313",
            "extra": "mean: 5.366002467456157 msec\nrounds: 169"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_h5md[periodic_1000]",
            "value": 26.50895931847402,
            "unit": "iter/sec",
            "range": "stddev: 0.0024979927543964664",
            "extra": "mean: 37.72309534999749 msec\nrounds: 20"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 229.89943800315226,
            "unit": "iter/sec",
            "range": "stddev: 0.0012408308067269982",
            "extra": "mean: 4.349727901406564 msec\nrounds: 213"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 18.999157848648093,
            "unit": "iter/sec",
            "range": "stddev: 0.04076700697477462",
            "extra": "mean: 52.633911880002415 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[periodic_100]",
            "value": 221.34873996136764,
            "unit": "iter/sec",
            "range": "stddev: 0.009629840396508084",
            "extra": "mean: 4.517757815899614 msec\nrounds: 239"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 23.263789800834545,
            "unit": "iter/sec",
            "range": "stddev: 0.030518860600840587",
            "extra": "mean: 42.9852577142924 msec\nrounds: 28"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[ethanol_100]",
            "value": 132.9311202939895,
            "unit": "iter/sec",
            "range": "stddev: 0.0013931570853542305",
            "extra": "mean: 7.522692938932639 msec\nrounds: 131"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[ethanol_1000]",
            "value": 13.136255314324801,
            "unit": "iter/sec",
            "range": "stddev: 0.04112128295752719",
            "extra": "mean: 76.12519519999903 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[periodic_100]",
            "value": 147.90094127395054,
            "unit": "iter/sec",
            "range": "stddev: 0.0005897051962263251",
            "extra": "mean: 6.7612821891900134 msec\nrounds: 148"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_asebytes_redis[periodic_1000]",
            "value": 16.129687695732738,
            "unit": "iter/sec",
            "range": "stddev: 0.004284143812287583",
            "extra": "mean: 61.997480599984556 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[ethanol_100]",
            "value": 61.52259541458829,
            "unit": "iter/sec",
            "range": "stddev: 0.0007410949538148683",
            "extra": "mean: 16.254190728807895 msec\nrounds: 59"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[ethanol_1000]",
            "value": 5.772258704266165,
            "unit": "iter/sec",
            "range": "stddev: 0.015656166640020914",
            "extra": "mean: 173.24240842859646 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[periodic_100]",
            "value": 46.35747126887425,
            "unit": "iter/sec",
            "range": "stddev: 0.0008446062638039212",
            "extra": "mean: 21.57149586956502 msec\nrounds: 46"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_aselmdb[periodic_1000]",
            "value": 4.031149287152116,
            "unit": "iter/sec",
            "range": "stddev: 0.07471965635779787",
            "extra": "mean: 248.06821299998774 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[ethanol_100]",
            "value": 53.71200937979109,
            "unit": "iter/sec",
            "range": "stddev: 0.0006747567689233456",
            "extra": "mean: 18.617810272729166 msec\nrounds: 55"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[ethanol_1000]",
            "value": 7.082694603761739,
            "unit": "iter/sec",
            "range": "stddev: 0.007047894875458528",
            "extra": "mean: 141.189202124977 msec\nrounds: 8"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[periodic_100]",
            "value": 57.48811928966934,
            "unit": "iter/sec",
            "range": "stddev: 0.0014335688806004303",
            "extra": "mean: 17.394898500005386 msec\nrounds: 58"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_znh5md[periodic_1000]",
            "value": 7.620341509491971,
            "unit": "iter/sec",
            "range": "stddev: 0.002556560834231718",
            "extra": "mean: 131.22771449998538 msec\nrounds: 8"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[ethanol_100]",
            "value": 29.080654061772734,
            "unit": "iter/sec",
            "range": "stddev: 0.003613645832187275",
            "extra": "mean: 34.387122032255995 msec\nrounds: 31"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[ethanol_1000]",
            "value": 3.087530490274234,
            "unit": "iter/sec",
            "range": "stddev: 0.005253093841152519",
            "extra": "mean: 323.88344120001875 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[periodic_100]",
            "value": 29.51655269285427,
            "unit": "iter/sec",
            "range": "stddev: 0.0017607480940484736",
            "extra": "mean: 33.87929513334029 msec\nrounds: 30"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_extxyz[periodic_1000]",
            "value": 2.8428390685086513,
            "unit": "iter/sec",
            "range": "stddev: 0.020264650163613653",
            "extra": "mean: 351.76103040000726 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[ethanol_100]",
            "value": 32.798373581962785,
            "unit": "iter/sec",
            "range": "stddev: 0.0010267535303112479",
            "extra": "mean: 30.489316718739445 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[ethanol_1000]",
            "value": 3.2629802275238653,
            "unit": "iter/sec",
            "range": "stddev: 0.004674720145123161",
            "extra": "mean: 306.4682990000392 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[periodic_100]",
            "value": 31.85471586102454,
            "unit": "iter/sec",
            "range": "stddev: 0.00160473726613061",
            "extra": "mean: 31.39252612902877 msec\nrounds: 31"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_trajectory_sqlite[periodic_1000]",
            "value": 3.150256383143337,
            "unit": "iter/sec",
            "range": "stddev: 0.0050431433031776374",
            "extra": "mean: 317.4344809999866 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[ethanol_100]",
            "value": 214.94129136665586,
            "unit": "iter/sec",
            "range": "stddev: 0.0002630479101519214",
            "extra": "mean: 4.652433199976258 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[ethanol_1000]",
            "value": 17.306987740826177,
            "unit": "iter/sec",
            "range": "stddev: 0.04003852369358555",
            "extra": "mean: 57.780129909092054 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[periodic_100]",
            "value": 225.87216584066908,
            "unit": "iter/sec",
            "range": "stddev: 0.0008191529559317477",
            "extra": "mean: 4.427283000001882 msec\nrounds: 233"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_lmdb[periodic_1000]",
            "value": 22.586880356727214,
            "unit": "iter/sec",
            "range": "stddev: 0.004147217188918559",
            "extra": "mean: 44.273489043481945 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[ethanol_100]",
            "value": 1.3916687410138957,
            "unit": "iter/sec",
            "range": "stddev: 0.013184573025750691",
            "extra": "mean: 718.5618031999866 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[ethanol_1000]",
            "value": 0.1371920801648074,
            "unit": "iter/sec",
            "range": "stddev: 0.16514475731647044",
            "extra": "mean: 7.2890504962000024 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[periodic_100]",
            "value": 1.475547583270345,
            "unit": "iter/sec",
            "range": "stddev: 0.009606564063632077",
            "extra": "mean: 677.7145049999945 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_zarr[periodic_1000]",
            "value": 0.1475651177252876,
            "unit": "iter/sec",
            "range": "stddev: 0.07554286304474675",
            "extra": "mean: 6.776669279399994 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[ethanol_100]",
            "value": 11.216096096878012,
            "unit": "iter/sec",
            "range": "stddev: 0.0034180604863091337",
            "extra": "mean: 89.15758133334369 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[ethanol_1000]",
            "value": 1.1266755080754574,
            "unit": "iter/sec",
            "range": "stddev: 0.02069830343095252",
            "extra": "mean: 887.5669993999963 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[periodic_100]",
            "value": 14.678731202520918,
            "unit": "iter/sec",
            "range": "stddev: 0.0024152285230866254",
            "extra": "mean: 68.12577914283631 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_h5md[periodic_1000]",
            "value": 1.473147861766499,
            "unit": "iter/sec",
            "range": "stddev: 0.0058614307626338145",
            "extra": "mean: 678.8184852000313 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[ethanol_100]",
            "value": 22.400244867787773,
            "unit": "iter/sec",
            "range": "stddev: 0.002100181529168082",
            "extra": "mean: 44.64236913043885 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[ethanol_1000]",
            "value": 2.245582297272485,
            "unit": "iter/sec",
            "range": "stddev: 0.0030988414587910748",
            "extra": "mean: 445.3187937999928 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[periodic_100]",
            "value": 22.95360270552935,
            "unit": "iter/sec",
            "range": "stddev: 0.0011197382201098675",
            "extra": "mean: 43.56614570832088 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_mongodb[periodic_1000]",
            "value": 2.290233981598923,
            "unit": "iter/sec",
            "range": "stddev: 0.0032581902433476903",
            "extra": "mean: 436.6366092000135 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[ethanol_100]",
            "value": 31.04002163155671,
            "unit": "iter/sec",
            "range": "stddev: 0.0016632612573478699",
            "extra": "mean: 32.21647239392882 msec\nrounds: 33"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[ethanol_1000]",
            "value": 3.071933995236606,
            "unit": "iter/sec",
            "range": "stddev: 0.01954022682523309",
            "extra": "mean: 325.52782760001264 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[periodic_100]",
            "value": 31.624678317715507,
            "unit": "iter/sec",
            "range": "stddev: 0.0019702608062020914",
            "extra": "mean: 31.62087500000973 msec\nrounds: 33"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_asebytes_redis[periodic_1000]",
            "value": 3.15914012840798,
            "unit": "iter/sec",
            "range": "stddev: 0.004626084115768713",
            "extra": "mean: 316.5418307999971 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[ethanol_100]",
            "value": 58.76609461359105,
            "unit": "iter/sec",
            "range": "stddev: 0.0012159662833806973",
            "extra": "mean: 17.016614879300253 msec\nrounds: 58"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[ethanol_1000]",
            "value": 5.832053401732735,
            "unit": "iter/sec",
            "range": "stddev: 0.003628779731693401",
            "extra": "mean: 171.46619400002314 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[periodic_100]",
            "value": 43.585351383380576,
            "unit": "iter/sec",
            "range": "stddev: 0.002830340814791547",
            "extra": "mean: 22.94348831110508 msec\nrounds: 45"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_aselmdb[periodic_1000]",
            "value": 4.44294349965112,
            "unit": "iter/sec",
            "range": "stddev: 0.003388239602447785",
            "extra": "mean: 225.07601100003285 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[ethanol_100]",
            "value": 2.1784847832291607,
            "unit": "iter/sec",
            "range": "stddev: 0.003625091038511852",
            "extra": "mean: 459.03465000003507 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[ethanol_1000]",
            "value": 0.21507242077447825,
            "unit": "iter/sec",
            "range": "stddev: 0.03503052603634939",
            "extra": "mean: 4.649596616799999 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[periodic_100]",
            "value": 2.4415475080678353,
            "unit": "iter/sec",
            "range": "stddev: 0.004460100832690104",
            "extra": "mean: 409.5763021999801 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_znh5md[periodic_1000]",
            "value": 0.2395369015452577,
            "unit": "iter/sec",
            "range": "stddev: 0.06857518051568978",
            "extra": "mean: 4.1747221139998825 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[ethanol_100]",
            "value": 18.18767036498722,
            "unit": "iter/sec",
            "range": "stddev: 0.0018610322378780375",
            "extra": "mean: 54.982302842099195 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[ethanol_1000]",
            "value": 1.822275887647679,
            "unit": "iter/sec",
            "range": "stddev: 0.008641975347352813",
            "extra": "mean: 548.7643264000326 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[periodic_100]",
            "value": 18.205023751040628,
            "unit": "iter/sec",
            "range": "stddev: 0.0024978319991412596",
            "extra": "mean: 54.9298926315786 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_read.py::test_read_single_sqlite[periodic_1000]",
            "value": 1.7583906261428244,
            "unit": "iter/sec",
            "range": "stddev: 0.01871104076115717",
            "extra": "mean: 568.7018487999921 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 1706.3391812389516,
            "unit": "iter/sec",
            "range": "stddev: 0.00012888767090596682",
            "extra": "mean: 586.0499547774039 usec\nrounds: 973"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 212.1265503179282,
            "unit": "iter/sec",
            "range": "stddev: 0.0047776333302222826",
            "extra": "mean: 4.71416707857283 msec\nrounds: 140"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[periodic_100]",
            "value": 983.3343845677016,
            "unit": "iter/sec",
            "range": "stddev: 0.0026830703214251253",
            "extra": "mean: 1.0169480653721115 msec\nrounds: 826"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 103.16349758216317,
            "unit": "iter/sec",
            "range": "stddev: 0.010400801216254987",
            "extra": "mean: 9.693351073169689 msec\nrounds: 123"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[ethanol_100]",
            "value": 702.125084145789,
            "unit": "iter/sec",
            "range": "stddev: 0.00006122730510787823",
            "extra": "mean: 1.4242476484323419 msec\nrounds: 640"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 92.29829026855988,
            "unit": "iter/sec",
            "range": "stddev: 0.0003918797972500505",
            "extra": "mean: 10.834436879494787 msec\nrounds: 83"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[periodic_100]",
            "value": 694.2546998587536,
            "unit": "iter/sec",
            "range": "stddev: 0.00014822877269206558",
            "extra": "mean: 1.4403935619066754 msec\nrounds: 630"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_zarr[periodic_1000]",
            "value": 92.54153291862414,
            "unit": "iter/sec",
            "range": "stddev: 0.000393822101589499",
            "extra": "mean: 10.805958886366668 msec\nrounds: 88"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[ethanol_100]",
            "value": 4720.334908599775,
            "unit": "iter/sec",
            "range": "stddev: 0.000011913520063491738",
            "extra": "mean: 211.84937496238732 usec\nrounds: 3539"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 2220.3778484402073,
            "unit": "iter/sec",
            "range": "stddev: 0.000017784357521976598",
            "extra": "mean: 450.37379592959354 usec\nrounds: 1720"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[periodic_100]",
            "value": 4764.462912207814,
            "unit": "iter/sec",
            "range": "stddev: 0.000011122599322415304",
            "extra": "mean: 209.88724614431052 usec\nrounds: 3502"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_h5md[periodic_1000]",
            "value": 2292.9929516242555,
            "unit": "iter/sec",
            "range": "stddev: 0.00001635538038160606",
            "extra": "mean: 436.1112402424281 usec\nrounds: 1794"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 290.617454299708,
            "unit": "iter/sec",
            "range": "stddev: 0.00031056682706429896",
            "extra": "mean: 3.440949554835477 msec\nrounds: 155"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 37.79576483976491,
            "unit": "iter/sec",
            "range": "stddev: 0.0005656860870724327",
            "extra": "mean: 26.457990842082406 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[periodic_100]",
            "value": 295.7060893937224,
            "unit": "iter/sec",
            "range": "stddev: 0.00008398217519765121",
            "extra": "mean: 3.3817362437488896 msec\nrounds: 160"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 37.35670280109631,
            "unit": "iter/sec",
            "range": "stddev: 0.0004520321085672126",
            "extra": "mean: 26.768957777790092 msec\nrounds: 18"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[ethanol_100]",
            "value": 477.2302071634774,
            "unit": "iter/sec",
            "range": "stddev: 0.000054076814789403796",
            "extra": "mean: 2.09542477611323 msec\nrounds: 469"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[ethanol_1000]",
            "value": 71.29624320917495,
            "unit": "iter/sec",
            "range": "stddev: 0.0005100929805037058",
            "extra": "mean: 14.025984469702218 msec\nrounds: 66"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[periodic_100]",
            "value": 429.00372605081185,
            "unit": "iter/sec",
            "range": "stddev: 0.00045508090983751356",
            "extra": "mean: 2.330982085413306 msec\nrounds: 480"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_asebytes_redis[periodic_1000]",
            "value": 72.63894925635196,
            "unit": "iter/sec",
            "range": "stddev: 0.00020113361623798375",
            "extra": "mean: 13.766718960524534 msec\nrounds: 76"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[ethanol_100]",
            "value": 16.132393520316178,
            "unit": "iter/sec",
            "range": "stddev: 0.0019495267938385503",
            "extra": "mean: 61.98708199999333 msec\nrounds: 17"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[ethanol_1000]",
            "value": 1.5271185925830828,
            "unit": "iter/sec",
            "range": "stddev: 0.013717863769947663",
            "extra": "mean: 654.8279910000474 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[periodic_100]",
            "value": 11.490284578319653,
            "unit": "iter/sec",
            "range": "stddev: 0.0024963384579343305",
            "extra": "mean: 87.03004639996834 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_aselmdb[periodic_1000]",
            "value": 1.140067288755216,
            "unit": "iter/sec",
            "range": "stddev: 0.007211944318663949",
            "extra": "mean: 877.1412089999103 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[ethanol_100]",
            "value": 5.927910707527073,
            "unit": "iter/sec",
            "range": "stddev: 0.0029733326615941887",
            "extra": "mean: 168.69349916661727 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[ethanol_1000]",
            "value": 0.49950923103164774,
            "unit": "iter/sec",
            "range": "stddev: 0.013372577317144854",
            "extra": "mean: 2.0019650045999695 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[periodic_100]",
            "value": 5.7926469317677345,
            "unit": "iter/sec",
            "range": "stddev: 0.004664258582422061",
            "extra": "mean: 172.63265166669348 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_update.py::test_update_property_trajectory_sqlite[periodic_1000]",
            "value": 0.5167313204167323,
            "unit": "iter/sec",
            "range": "stddev: 0.09072232609527912",
            "extra": "mean: 1.9352417020000303 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[ethanol_100]",
            "value": 198.68327392512458,
            "unit": "iter/sec",
            "range": "stddev: 0.001392615918417716",
            "extra": "mean: 5.033136309082858 msec\nrounds: 165"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[ethanol_1000]",
            "value": 20.499493624771887,
            "unit": "iter/sec",
            "range": "stddev: 0.02868945950105396",
            "extra": "mean: 48.781692772722224 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[periodic_100]",
            "value": 221.79264202427876,
            "unit": "iter/sec",
            "range": "stddev: 0.00022006866967341947",
            "extra": "mean: 4.5087158477084825 msec\nrounds: 197"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_lmdb[periodic_1000]",
            "value": 21.21994027248263,
            "unit": "iter/sec",
            "range": "stddev: 0.027755732610896314",
            "extra": "mean: 47.125486083331225 msec\nrounds: 24"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[ethanol_100]",
            "value": 9.902074630191334,
            "unit": "iter/sec",
            "range": "stddev: 0.004004807014929646",
            "extra": "mean: 100.98893790913363 msec\nrounds: 11"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[ethanol_1000]",
            "value": 1.780081402481562,
            "unit": "iter/sec",
            "range": "stddev: 0.0019991769637723853",
            "extra": "mean: 561.7720620000455 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[periodic_100]",
            "value": 5.7233028830994,
            "unit": "iter/sec",
            "range": "stddev: 0.01548089860098126",
            "extra": "mean: 174.7242842857304 msec\nrounds: 7"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_zarr[periodic_1000]",
            "value": 0.7568629645627607,
            "unit": "iter/sec",
            "range": "stddev: 0.06228484988703391",
            "extra": "mean: 1.321243140200022 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[ethanol_100]",
            "value": 24.027018717029712,
            "unit": "iter/sec",
            "range": "stddev: 0.002471332083568851",
            "extra": "mean: 41.61981191995437 msec\nrounds: 25"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[ethanol_1000]",
            "value": 3.007487484750721,
            "unit": "iter/sec",
            "range": "stddev: 0.002853763922023498",
            "extra": "mean: 332.50346180007 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[periodic_100]",
            "value": 42.07842994350283,
            "unit": "iter/sec",
            "range": "stddev: 0.0002312813964706994",
            "extra": "mean: 23.765145261899352 msec\nrounds: 42"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_h5md[periodic_1000]",
            "value": 5.343898096367185,
            "unit": "iter/sec",
            "range": "stddev: 0.0012140609818785495",
            "extra": "mean: 187.1293168333068 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[ethanol_100]",
            "value": 57.252890655642716,
            "unit": "iter/sec",
            "range": "stddev: 0.0016345078755561726",
            "extra": "mean: 17.466366999959366 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[ethanol_1000]",
            "value": 12.508527698529925,
            "unit": "iter/sec",
            "range": "stddev: 0.0484001566864821",
            "extra": "mean: 79.94545993750535 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[periodic_100]",
            "value": 55.769782047677815,
            "unit": "iter/sec",
            "range": "stddev: 0.0022543109022290625",
            "extra": "mean: 17.93085723636316 msec\nrounds: 55"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_mongodb[periodic_1000]",
            "value": 13.07674660723404,
            "unit": "iter/sec",
            "range": "stddev: 0.03910695515156126",
            "extra": "mean: 76.47162019999692 msec\nrounds: 15"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[ethanol_100]",
            "value": 130.48693432338558,
            "unit": "iter/sec",
            "range": "stddev: 0.0021073537045523624",
            "extra": "mean: 7.66360252990312 msec\nrounds: 117"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[ethanol_1000]",
            "value": 13.423663169970089,
            "unit": "iter/sec",
            "range": "stddev: 0.03659829014307051",
            "extra": "mean: 74.49531378566527 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[periodic_100]",
            "value": 142.76510874813098,
            "unit": "iter/sec",
            "range": "stddev: 0.0006537021462009748",
            "extra": "mean: 7.004512578519586 msec\nrounds: 121"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_asebytes_redis[periodic_1000]",
            "value": 16.938686963877657,
            "unit": "iter/sec",
            "range": "stddev: 0.0020499048259249373",
            "extra": "mean: 59.03645318745987 msec\nrounds: 16"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[ethanol_100]",
            "value": 9.443760959062512,
            "unit": "iter/sec",
            "range": "stddev: 0.0030079241460107577",
            "extra": "mean: 105.89001610003379 msec\nrounds: 10"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[ethanol_1000]",
            "value": 0.949373645895321,
            "unit": "iter/sec",
            "range": "stddev: 0.0456479556078265",
            "extra": "mean: 1.0533260579999932 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[periodic_100]",
            "value": 7.477511724650582,
            "unit": "iter/sec",
            "range": "stddev: 0.0032348544057149097",
            "extra": "mean: 133.73432724998224 msec\nrounds: 8"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_aselmdb[periodic_1000]",
            "value": 0.7142692150750152,
            "unit": "iter/sec",
            "range": "stddev: 0.04711956661322133",
            "extra": "mean: 1.40003233919997 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[ethanol_100]",
            "value": 55.34409145843409,
            "unit": "iter/sec",
            "range": "stddev: 0.00019267829647953656",
            "extra": "mean: 18.0687761538383 msec\nrounds: 52"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[ethanol_1000]",
            "value": 19.14206094854253,
            "unit": "iter/sec",
            "range": "stddev: 0.00047925550819610834",
            "extra": "mean: 52.24097878949339 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[periodic_100]",
            "value": 54.249020417678636,
            "unit": "iter/sec",
            "range": "stddev: 0.000148596472775535",
            "extra": "mean: 18.433512574065222 msec\nrounds: 54"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_znh5md[periodic_1000]",
            "value": 13.280543098625179,
            "unit": "iter/sec",
            "range": "stddev: 0.0005704281511370282",
            "extra": "mean: 75.29812542858443 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[ethanol_100]",
            "value": 50.938349738431164,
            "unit": "iter/sec",
            "range": "stddev: 0.00019242077815988668",
            "extra": "mean: 19.631574346931302 msec\nrounds: 49"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[ethanol_1000]",
            "value": 5.0695685099864445,
            "unit": "iter/sec",
            "range": "stddev: 0.0013474066736174056",
            "extra": "mean: 197.25544650005608 msec\nrounds: 6"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[periodic_100]",
            "value": 33.77013841979155,
            "unit": "iter/sec",
            "range": "stddev: 0.00040377285292766767",
            "extra": "mean: 29.611960352935164 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_extxyz[periodic_1000]",
            "value": 3.199984422987716,
            "unit": "iter/sec",
            "range": "stddev: 0.03411746768351465",
            "extra": "mean: 312.50152120001076 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[ethanol_100]",
            "value": 4.425883916023918,
            "unit": "iter/sec",
            "range": "stddev: 0.005294130003841288",
            "extra": "mean: 225.94356720010182 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[ethanol_1000]",
            "value": 0.4513637757387488,
            "unit": "iter/sec",
            "range": "stddev: 0.04505737252411917",
            "extra": "mean: 2.215507875799949 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[periodic_100]",
            "value": 4.6158312006042514,
            "unit": "iter/sec",
            "range": "stddev: 0.007160746508949457",
            "extra": "mean: 216.6457039999841 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_trajectory_sqlite[periodic_1000]",
            "value": 0.4568348671157303,
            "unit": "iter/sec",
            "range": "stddev: 0.048437007399085574",
            "extra": "mean: 2.188974774000053 sec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[ethanol_100]",
            "value": 184.24701622330196,
            "unit": "iter/sec",
            "range": "stddev: 0.0005333353978626067",
            "extra": "mean: 5.42749630630669 msec\nrounds: 111"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[ethanol_1000]",
            "value": 183.34528150587053,
            "unit": "iter/sec",
            "range": "stddev: 0.0008578029161327412",
            "extra": "mean: 5.45418999489213 msec\nrounds: 196"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[periodic_100]",
            "value": 168.1588207032127,
            "unit": "iter/sec",
            "range": "stddev: 0.0007933694740366529",
            "extra": "mean: 5.94675911628164 msec\nrounds: 172"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_lmdb[periodic_1000]",
            "value": 167.3449794068557,
            "unit": "iter/sec",
            "range": "stddev: 0.0008210073484209359",
            "extra": "mean: 5.975679721880156 msec\nrounds: 169"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[ethanol_100]",
            "value": 1.8126335610715179,
            "unit": "iter/sec",
            "range": "stddev: 0.037448964000854325",
            "extra": "mean: 551.6834850000578 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[ethanol_1000]",
            "value": 1.875160768315145,
            "unit": "iter/sec",
            "range": "stddev: 0.005109188560452332",
            "extra": "mean: 533.2876075999138 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[periodic_100]",
            "value": 2.1460887379949103,
            "unit": "iter/sec",
            "range": "stddev: 0.002012797321196217",
            "extra": "mean: 465.9639567999875 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_zarr[periodic_1000]",
            "value": 2.0608326812582805,
            "unit": "iter/sec",
            "range": "stddev: 0.038775811975813174",
            "extra": "mean: 485.240752000027 msec\nrounds: 5"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[ethanol_100]",
            "value": 18.87979099253691,
            "unit": "iter/sec",
            "range": "stddev: 0.00033979775309799014",
            "extra": "mean: 52.96668805260053 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[ethanol_1000]",
            "value": 18.890300680362536,
            "unit": "iter/sec",
            "range": "stddev: 0.0005042743475379046",
            "extra": "mean: 52.93721984211468 msec\nrounds: 19"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[periodic_100]",
            "value": 21.589106644728304,
            "unit": "iter/sec",
            "range": "stddev: 0.00019717605644620226",
            "extra": "mean: 46.31965631816373 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_h5md[periodic_1000]",
            "value": 21.525573792085357,
            "unit": "iter/sec",
            "range": "stddev: 0.0003356543339905427",
            "extra": "mean: 46.456369045441456 msec\nrounds: 22"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[ethanol_100]",
            "value": 37.28819083582759,
            "unit": "iter/sec",
            "range": "stddev: 0.0006086481794228382",
            "extra": "mean: 26.818142086935755 msec\nrounds: 23"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[ethanol_1000]",
            "value": 36.83434156375706,
            "unit": "iter/sec",
            "range": "stddev: 0.000643655658207475",
            "extra": "mean: 27.148578135137466 msec\nrounds: 37"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[periodic_100]",
            "value": 36.20509547304829,
            "unit": "iter/sec",
            "range": "stddev: 0.0007855277670680119",
            "extra": "mean: 27.62042157144476 msec\nrounds: 35"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_mongodb[periodic_1000]",
            "value": 36.67686020911136,
            "unit": "iter/sec",
            "range": "stddev: 0.0007561297625215268",
            "extra": "mean: 27.265147406254187 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[ethanol_100]",
            "value": 158.4843942284273,
            "unit": "iter/sec",
            "range": "stddev: 0.0004533919756385225",
            "extra": "mean: 6.309769519380414 msec\nrounds: 129"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[ethanol_1000]",
            "value": 153.61665091238046,
            "unit": "iter/sec",
            "range": "stddev: 0.0007683636243020146",
            "extra": "mean: 6.509710985499729 msec\nrounds: 138"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[periodic_100]",
            "value": 166.27669275437228,
            "unit": "iter/sec",
            "range": "stddev: 0.00021271212510565993",
            "extra": "mean: 6.014071987089753 msec\nrounds: 155"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_asebytes_redis[periodic_1000]",
            "value": 165.81110153291567,
            "unit": "iter/sec",
            "range": "stddev: 0.00029966047268536214",
            "extra": "mean: 6.030959270851276 msec\nrounds: 144"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[ethanol_100]",
            "value": 81.48256567828882,
            "unit": "iter/sec",
            "range": "stddev: 0.000618851821590334",
            "extra": "mean: 12.272563973356228 msec\nrounds: 75"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[ethanol_1000]",
            "value": 80.6154393854411,
            "unit": "iter/sec",
            "range": "stddev: 0.0010820463246461283",
            "extra": "mean: 12.404571725011238 msec\nrounds: 80"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[periodic_100]",
            "value": 71.74410192051529,
            "unit": "iter/sec",
            "range": "stddev: 0.0007315936889818994",
            "extra": "mean: 13.938428013328425 msec\nrounds: 75"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_aselmdb[periodic_1000]",
            "value": 71.34346286919414,
            "unit": "iter/sec",
            "range": "stddev: 0.0016472327411804256",
            "extra": "mean: 14.016701177422052 msec\nrounds: 62"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[ethanol_100]",
            "value": 11.15191515291871,
            "unit": "iter/sec",
            "range": "stddev: 0.00018858917580320087",
            "extra": "mean: 89.6706965832929 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[ethanol_1000]",
            "value": 11.059842922504895,
            "unit": "iter/sec",
            "range": "stddev: 0.0017714016673565415",
            "extra": "mean: 90.41719733335185 msec\nrounds: 12"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[periodic_100]",
            "value": 12.020772674819185,
            "unit": "iter/sec",
            "range": "stddev: 0.00886300796573012",
            "extra": "mean: 83.18932792854282 msec\nrounds: 14"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_znh5md[periodic_1000]",
            "value": 12.707328172283514,
            "unit": "iter/sec",
            "range": "stddev: 0.010011654029779693",
            "extra": "mean: 78.69474892299877 msec\nrounds: 13"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[ethanol_100]",
            "value": 378.4721933442342,
            "unit": "iter/sec",
            "range": "stddev: 0.00005137989384591233",
            "extra": "mean: 2.6422020364662924 msec\nrounds: 329"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[ethanol_1000]",
            "value": 376.74257410002394,
            "unit": "iter/sec",
            "range": "stddev: 0.00008031028058569722",
            "extra": "mean: 2.6543323445427838 msec\nrounds: 357"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[periodic_100]",
            "value": 274.7219232673463,
            "unit": "iter/sec",
            "range": "stddev: 0.0004159054481723568",
            "extra": "mean: 3.6400444060186907 msec\nrounds: 266"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_extxyz[periodic_1000]",
            "value": 278.6106279017526,
            "unit": "iter/sec",
            "range": "stddev: 0.00006069042705125256",
            "extra": "mean: 3.5892385280888615 msec\nrounds: 267"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[ethanol_100]",
            "value": 34.0848801219554,
            "unit": "iter/sec",
            "range": "stddev: 0.0015355594396883302",
            "extra": "mean: 29.338521843762067 msec\nrounds: 32"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[ethanol_1000]",
            "value": 32.76917644526287,
            "unit": "iter/sec",
            "range": "stddev: 0.002405851864381845",
            "extra": "mean: 30.51648251430379 msec\nrounds: 35"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[periodic_100]",
            "value": 32.72817490830746,
            "unit": "iter/sec",
            "range": "stddev: 0.002233672564545993",
            "extra": "mean: 30.554713264691333 msec\nrounds: 34"
          },
          {
            "name": "tests/benchmarks/test_bench_write.py::test_write_single_sqlite[periodic_1000]",
            "value": 32.283807360697395,
            "unit": "iter/sec",
            "range": "stddev: 0.0014063298666921738",
            "extra": "mean: 30.975280852945776 msec\nrounds: 34"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_encode_current",
            "value": 44640.30487793835,
            "unit": "iter/sec",
            "range": "stddev: 0.0000029179168892832713",
            "extra": "mean: 22.401280697664077 usec\nrounds: 11418"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_atoms_to_dict_new",
            "value": 234897.18814809885,
            "unit": "iter/sec",
            "range": "stddev: 7.509904395511665e-7",
            "extra": "mean: 4.257181654169126 usec\nrounds: 38199"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_decode_current",
            "value": 43083.62484803913,
            "unit": "iter/sec",
            "range": "stddev: 0.000029571754582589073",
            "extra": "mean: 23.210674671110294 usec\nrounds: 15824"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_dict_to_atoms_new",
            "value": 159552.48582716292,
            "unit": "iter/sec",
            "range": "stddev: 0.000016468545219045874",
            "extra": "mean: 6.26753005329708 usec\nrounds: 55085"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_read_current_aseio",
            "value": 23.72169384975357,
            "unit": "iter/sec",
            "range": "stddev: 0.04154975526159216",
            "extra": "mean: 42.155505687482275 msec\nrounds: 32"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_read_new_aseio",
            "value": 23.160906077231175,
            "unit": "iter/sec",
            "range": "stddev: 0.04611694976856758",
            "extra": "mean: 43.176203757549516 msec\nrounds: 33"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_write_current_aseio",
            "value": 31.47443240976018,
            "unit": "iter/sec",
            "range": "stddev: 0.0006469166227586936",
            "extra": "mean: 31.771819964254586 msec\nrounds: 28"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_write_new_aseio",
            "value": 31.5222437261831,
            "unit": "iter/sec",
            "range": "stddev: 0.0012190532039217875",
            "extra": "mean: 31.7236301034427 msec\nrounds: 29"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_random_access_current",
            "value": 24.1450289403113,
            "unit": "iter/sec",
            "range": "stddev: 0.04384661153731675",
            "extra": "mean: 41.41639268571973 msec\nrounds: 35"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_random_access_new",
            "value": 22.265806610931904,
            "unit": "iter/sec",
            "range": "stddev: 0.04796546471130347",
            "extra": "mean: 44.91191437497832 msec\nrounds: 32"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_via_view",
            "value": 107.93258732194676,
            "unit": "iter/sec",
            "range": "stddev: 0.020566848488689837",
            "extra": "mean: 9.26504241964616 msec\nrounds: 112"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_manual_loop",
            "value": 37.12339024188187,
            "unit": "iter/sec",
            "range": "stddev: 0.0005488771029642353",
            "extra": "mean: 26.937194945945965 msec\nrounds: 37"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_column_read_selective_keys",
            "value": 892.9710643038493,
            "unit": "iter/sec",
            "range": "stddev: 0.00003994596772585904",
            "extra": "mean: 1.1198571151682157 msec\nrounds: 712"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_row_view_iteration",
            "value": 24.230211980625825,
            "unit": "iter/sec",
            "range": "stddev: 0.04515255223177622",
            "extra": "mean: 41.270790400000934 msec\nrounds: 35"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_direct_iteration",
            "value": 22.596706374003713,
            "unit": "iter/sec",
            "range": "stddev: 0.04711967151206744",
            "extra": "mean: 44.254237031218224 msec\nrounds: 32"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_multi_column_view",
            "value": 89.55146059162837,
            "unit": "iter/sec",
            "range": "stddev: 0.0017228007947393453",
            "extra": "mean: 11.166763706514956 msec\nrounds: 92"
          },
          {
            "name": "tests/test_benchmark_backend.py::test_multi_column_manual",
            "value": 36.817666351630606,
            "unit": "iter/sec",
            "range": "stddev: 0.0006677263509163616",
            "extra": "mean: 27.160874088254413 msec\nrounds: 34"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[ethanol_100]",
            "value": 210.4024368327221,
            "unit": "iter/sec",
            "range": "stddev: 0.00017227899905013702",
            "extra": "mean: 4.7527966645891935 msec\nrounds: 161"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[ethanol_1000]",
            "value": 17.335339649896337,
            "unit": "iter/sec",
            "range": "stddev: 0.04292014846749339",
            "extra": "mean: 57.68563063637347 msec\nrounds: 22"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[periodic_100]",
            "value": 209.97677227066012,
            "unit": "iter/sec",
            "range": "stddev: 0.0006066091734459286",
            "extra": "mean: 4.762431526049937 msec\nrounds: 192"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_lmdb[periodic_1000]",
            "value": 21.10158935790115,
            "unit": "iter/sec",
            "range": "stddev: 0.029404110489564816",
            "extra": "mean: 47.38979529167864 msec\nrounds: 24"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[ethanol_100]",
            "value": 9.951813346914935,
            "unit": "iter/sec",
            "range": "stddev: 0.0010956756059641247",
            "extra": "mean: 100.48419972727888 msec\nrounds: 11"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[ethanol_1000]",
            "value": 1.7400355982748734,
            "unit": "iter/sec",
            "range": "stddev: 0.004754651923815759",
            "extra": "mean: 574.7008859999369 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[periodic_100]",
            "value": 6.024551989260986,
            "unit": "iter/sec",
            "range": "stddev: 0.001024612208667456",
            "extra": "mean: 165.98744633336082 msec\nrounds: 6"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_zarr[periodic_1000]",
            "value": 0.7471596081948538,
            "unit": "iter/sec",
            "range": "stddev: 0.06353791952873654",
            "extra": "mean: 1.3384021152000058 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[ethanol_100]",
            "value": 24.788332453965445,
            "unit": "iter/sec",
            "range": "stddev: 0.0003928947817129883",
            "extra": "mean: 40.34155995999754 msec\nrounds: 25"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[ethanol_1000]",
            "value": 2.888040872677651,
            "unit": "iter/sec",
            "range": "stddev: 0.016509439837516602",
            "extra": "mean: 346.25548739995793 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[periodic_100]",
            "value": 41.34411094640878,
            "unit": "iter/sec",
            "range": "stddev: 0.0002611122111817002",
            "extra": "mean: 24.187241595211077 msec\nrounds: 42"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_asebytes_h5md[periodic_1000]",
            "value": 5.291062116266391,
            "unit": "iter/sec",
            "range": "stddev: 0.0004393578152545675",
            "extra": "mean: 188.99797016664857 msec\nrounds: 6"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[ethanol_100]",
            "value": 9.529263293629018,
            "unit": "iter/sec",
            "range": "stddev: 0.0014034646507901521",
            "extra": "mean: 104.93990659997507 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[ethanol_1000]",
            "value": 0.9409481826552599,
            "unit": "iter/sec",
            "range": "stddev: 0.05236947531654866",
            "extra": "mean: 1.0627577781999662 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[periodic_100]",
            "value": 7.276389168496481,
            "unit": "iter/sec",
            "range": "stddev: 0.0014386556171429004",
            "extra": "mean: 137.4308021249817 msec\nrounds: 8"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_aselmdb[periodic_1000]",
            "value": 0.7121718343504855,
            "unit": "iter/sec",
            "range": "stddev: 0.05694704860493745",
            "extra": "mean: 1.4041555026000423 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[ethanol_100]",
            "value": 55.34819224368565,
            "unit": "iter/sec",
            "range": "stddev: 0.00028599046274852696",
            "extra": "mean: 18.0674374259095 msec\nrounds: 54"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[ethanol_1000]",
            "value": 19.010600329764685,
            "unit": "iter/sec",
            "range": "stddev: 0.0006969165156728228",
            "extra": "mean: 52.602231526287525 msec\nrounds: 19"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[periodic_100]",
            "value": 53.73202457717534,
            "unit": "iter/sec",
            "range": "stddev: 0.0005483310685195303",
            "extra": "mean: 18.610875132086253 msec\nrounds: 53"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_znh5md[periodic_1000]",
            "value": 13.184808760565533,
            "unit": "iter/sec",
            "range": "stddev: 0.0004595036482365383",
            "extra": "mean: 75.84486192859329 msec\nrounds: 14"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[ethanol_100]",
            "value": 50.96054881057572,
            "unit": "iter/sec",
            "range": "stddev: 0.00021540407149179432",
            "extra": "mean: 19.623022580017278 msec\nrounds: 50"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[ethanol_1000]",
            "value": 5.124920286457161,
            "unit": "iter/sec",
            "range": "stddev: 0.0016850500289825347",
            "extra": "mean: 195.1249861666232 msec\nrounds: 6"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[periodic_100]",
            "value": 32.945900110105484,
            "unit": "iter/sec",
            "range": "stddev: 0.0018544076978604612",
            "extra": "mean: 30.35279038235384 msec\nrounds: 34"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_extxyz[periodic_1000]",
            "value": 3.3981455217527983,
            "unit": "iter/sec",
            "range": "stddev: 0.00046085350430697877",
            "extra": "mean: 294.27815660001215 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[ethanol_100]",
            "value": 4.541030990934453,
            "unit": "iter/sec",
            "range": "stddev: 0.0021267400610750593",
            "extra": "mean: 220.2143086000433 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[ethanol_1000]",
            "value": 0.4509637452263503,
            "unit": "iter/sec",
            "range": "stddev: 0.059646112561604236",
            "extra": "mean: 2.217473157399991 sec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[periodic_100]",
            "value": 4.432094816053332,
            "unit": "iter/sec",
            "range": "stddev: 0.005802213782890143",
            "extra": "mean: 225.62694199996258 msec\nrounds: 5"
          },
          {
            "name": "tests/test_benchmark_file_size.py::test_size_sqlite[periodic_1000]",
            "value": 0.4562019636479712,
            "unit": "iter/sec",
            "range": "stddev: 0.03850463600082871",
            "extra": "mean: 2.1920116082000276 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}