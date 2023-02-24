from py_arkworks_bls12381 import G1Point, G2Point, GT, Scalar


# Initilisation -- This is the generator point
gt_gen = GT()

# Zero/One
zero = GT.zero()
one = GT.one()

# Computing a pairing using pairing and multi_pairing
# multi_pairing does multiple pairings and adds them together with only one final_exp
assert gt_gen == GT.pairing(G1Point(), G2Point()) 
g1s = [G1Point()]
g2s = [G2Point()]
assert gt_gen == GT.multi_pairing(g1s, g2s)

# Bilinearity
a = Scalar(1234)
b = Scalar(4566)
c = a * b


g = G1Point() * a
h = G2Point() * b

p = GT.pairing(g, h)

c_g1 = G1Point() *c
c_g2 = G2Point() *c

assert p == GT.pairing(c_g1, G2Point())
assert p == GT.pairing(G1Point(), c_g2)
