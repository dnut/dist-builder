# dist-builder
Build a wheel and source distribution and bundle with other files in a zip

```python -m dist-builder```

## build.ini
By default, dist-builder expects setup.py to be in your current working directory, and it simply builds a wheel and source distribution. This is not particularly interesting, so add a build.ini file to customize your build. dist-builder will look in the current working directory for your build.ini, or you can specify it as an argument like this:

```python -m dist-builder /path/to/any-name-build.ini```