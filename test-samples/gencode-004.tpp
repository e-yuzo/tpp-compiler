inteiro: n
inteiro: soma

inteiro main()
	n := 10
	soma := 0
	repita
		soma := soma + n
		n := n - 1
	até n = 0
	escreva(soma)
	retorna(0)
fim
