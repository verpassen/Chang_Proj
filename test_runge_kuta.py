import numpy 

# solve the ode : dv/dt = 3*t**2 + 1
# analytical solution : v = t**3 + t + c   
def myfun(t,v):
 return 3*t**2 +1 
 
def analytical_sol(t,v):
 return t**3 + t
 
t=0
h=1 
v_init= 0 

k_1 = myfun(t,v_init) 
k_2 = myfun(t+0.5*h,v_init+0.5*k_1*h)

v_next = v_init + h*(0*k_1+ 1*k_2)
v_ana = analytical_sol(t+h,v_init)

print(f'next value of v is {v_next}')
print(f'next true value of v is {v_ana}')