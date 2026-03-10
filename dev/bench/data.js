window.BENCHMARK_DATA = {
  "lastUpdate": 1773143058908,
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
      }
    ]
  }
}