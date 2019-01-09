inteiro: A[5]
inteiro: B[5]

inteiro main()
    inteiro: a
    inteiro: i
    i := 0

    repita
        leia(a)
        A[i] := a
        i := i + 1
    até i = 5

    i := 0
    repita
        B[4 - i] := A[i]
        i := i + 1
    até i = 5
    
    i := 0
    repita
        escreva(B[i])
        i := i + 1
    até i = 5  

    retorna(0)
fim
