/usr/local/miniconda/lib/python3.7/site-packages/bids/layout/validation.py:46: UserWarning: The ability to pass arguments to BIDSLayout that control indexing is likely to be removed in future; possibly as early as PyBIDS 0.14. This includes the `config_filename`, `ignore`, `force_index`, and `index_metadata` arguments. The recommended usage pattern is to initialize a new BIDSLayoutIndexer with these arguments, and pass it to the BIDSLayout via the `indexer` argument.
  warnings.warn("The ability to pass arguments to BIDSLayout that control "
Traceback (most recent call last):
  File "/usr/local/miniconda/lib/python3.7/site-packages/bids/layout/index.py", line 280, in _index_metadata
    payload = json.load(handle)
  File "/usr/local/miniconda/lib/python3.7/json/__init__.py", line 296, in load
    parse_constant=parse_constant, object_pairs_hook=object_pairs_hook, **kw)
  File "/usr/local/miniconda/lib/python3.7/json/__init__.py", line 348, in loads
    return _default_decoder.decode(s)
  File "/usr/local/miniconda/lib/python3.7/json/decoder.py", line 340, in decode
    raise JSONDecodeError("Extra data", s, end)
json.decoder.JSONDecodeError: Extra data: line 1 column 18 (char 17)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/usr/local/miniconda/bin/fmriprep", line 10, in <module>
    sys.exit(main())
  File "/usr/local/miniconda/lib/python3.7/site-packages/fmriprep/cli/run.py", line 17, in main
    parse_args()
  File "/usr/local/miniconda/lib/python3.7/site-packages/fmriprep/cli/parser.py", line 602, in parse_args
    config.from_dict(vars(opts))
  File "/usr/local/miniconda/lib/python3.7/site-packages/fmriprep/config.py", line 617, in from_dict
    execution.load(settings)
  File "/usr/local/miniconda/lib/python3.7/site-packages/fmriprep/config.py", line 218, in load
    cls.init()
  File "/usr/local/miniconda/lib/python3.7/site-packages/fmriprep/config.py", line 453, in init
    re.compile(r"^\."),
  File "/usr/local/miniconda/lib/python3.7/site-packages/bids/layout/layout.py", line 155, in __init__
    indexer(self)
  File "/usr/local/miniconda/lib/python3.7/site-packages/bids/layout/index.py", line 111, in __call__
    self._index_metadata()
  File "/usr/local/miniconda/lib/python3.7/site-packages/bids/layout/index.py", line 284, in _index_metadata
    raise IOError(msg) from e
OSError: Error occurred while trying to decode JSON from file '/dartfs-hpc/rc/lab/C/CANlab/labdata/data/spacetop/dartmouth/.git/annex/transfer/download/590b4fd0-0142-4e9d-8964-d1158c242c6a/MD5E-s102739--2349cac048f4ccf45bcb15278a783d26.json'.
