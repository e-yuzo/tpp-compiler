#Tools:
    - LLVM 6.0.1
#To execute:
    - python3 parser.py [path to .tpp file]
    - llvm-as file.ll -o file.bc
    - llc file.bc -o file.s --mtriple x86_64-pc-linux-gnu
    - clang file.s -o exec -no-pie
    - ./exec
