# NOTE: this might be removed

Add a way of decide how the argparse section works. Example:
    [1] Single input            -> myprof x
    [2] Multiple input          -> myprof x y z
    [3] Single argument input   -> myprof --arg x
    [2] Multiple argument input -> myprof --arg x y z



Next step on module validator:
- Create a unit test that interacts with an example folder
tests/mocks/my_pyproj/pyproject.toml # Should reference 
```
   module_validator = "danfault.modules.module_validator:main"   (Correct)
   module_validatora = "danfault.modules.module_validator:maina" (Wrong)
   module_validator3 = "danfault.modules.module_validator:main3" (Wrong)
```

# Usage
```
 module_validator pyproject.toml
```