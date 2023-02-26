from .arkworks import G1 as ark_G1, G2 as ark_G2, pairing_check as ark_pairing
from .py_ecc_4844 import G1 as py_G1, G2 as py_G2,pairing_check as py_pairing

from timeit import timeit

def timeit_dic(module_name):
   return {
   0: {
      "method_name": "pairingsGen",
      "setup": "from {} import G1, G2, pairing_check".format(module_name),
      "statement": "pairing_check([[G1, G2], [G1, G2]])",
      "iterations": 10,
   },
   1: {
      "method_name": "pairings",
      "setup": "from {} import G1, G2, pairing_check, multiply; a = multiply(G1, 123456789);b = multiply(G2, 123456789)".format(module_name),
      "statement": "pairing_check([[G1, G2], [a, b]])",
      "iterations": 10,
   },
   2: {
      "method_name": "multiplyG1",
      "setup": "from {} import G1, multiply".format(module_name),
      "statement": "multiply(G1, 12345678910)",
      "iterations": 100,
   },
   4: {
      "method_name": "multiplyG2",
      "setup": "from {} import G2, multiply".format(module_name),
      "statement": "multiply(G2, 12345678910)",
      "iterations": 100,
   },
   5: {
      "method_name": "addG1",
      "setup": "from {} import G1, G2, add".format(module_name),
      "statement": "add(G1, G1)",
      "iterations": 100,
   },
   6: {
      "method_name": "addG2",
      "setup": "from {} import G2, add".format(module_name),
      "statement": "add(G2, G2)",
      "iterations": 100,
   },
   7: {
      "method_name": "G1_to_bytes48",
      "setup": "from {} import G1,G1_to_bytes48".format(module_name),
      "statement": "G1_to_bytes48(G1)",
      "iterations": 100,
   },
   8: {
      "method_name": "G2_to_bytes96",
      "setup": "from {} import G2,G2_to_bytes96".format(module_name),
      "statement": "G2_to_bytes96(G2)",
      "iterations": 100,
   },
   }

def run_benchmark(module_name):
   # Create timeit dictionary to specify
   # all of the benchmarks we want to run
   # py_ecc and arkworks have the same api
   # so we can template the dictionary and just 
   # pass the module name
   benches = timeit_dic(module_name)
   
   print(f"\n{module_name} benchmarks\n") 
   
   # Run benchmarks
   for id, library in benches.items():
      result = timeit(
         stmt=library["statement"],
         setup=library["setup"],
         number=library["iterations"],
         )
      # multiply by 1000 to turn seconds into milliseconds
      print(f"{library['method_name']}", (result / library["iterations"])*1000, "ms")

run_benchmark("arkworks")
run_benchmark("py_ecc_4844")