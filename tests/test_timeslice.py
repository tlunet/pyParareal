import sys
sys.path.append('../src')

from timeslice import timeslice
from integrator import integrator
from impeuler import impeuler
from solution_linear import solution_linear
import unittest
import numpy as np

class TestTimeslice(unittest.TestCase):

  def setUp(self):
    t = np.sort( np.random.rand(2) )
    nsteps_c        = 1+np.random.randint(25)
    nsteps_f        = 1+np.random.randint(125)
    self.int_coarse = impeuler(t[0], t[1], nsteps_c)
    self.int_fine   = impeuler(t[0], t[1], nsteps_f)
    self.ndofs           = [np.random.randint(25), np.random.randint(25)]
    self.ndof_c          = np.min(self.ndofs)
    self.ndof_f          = np.max(self.ndofs)
    self.u0_f            = np.random.rand(self.ndof_f)
    self.A_f             = np.random.rand(self.ndof_f, self.ndof_f)
    self.u0fine          = solution_linear(self.u0_f, self.A_f)
    self.u0_c            = np.random.rand(self.ndof_c)
    self.A_c             = np.random.rand(self.ndof_c, self.ndof_c)
    self.u0coarse        = solution_linear(self.u0_f, self.A_f)
    # TODO: randomise tolerance and iteration number

  # Timeslice can be instantiated
  def test_caninstantiate(self):
    ts = timeslice(self.int_fine, self.int_coarse, 1e-10, 5, self.u0fine, self.u0fine)
    
  def test_cansinstanatiatewithu0coarse(self):
    ts = timeslice(self.int_fine, self.int_coarse, 1e-10, 5, self.u0fine, self.u0fine)

  # Negative tolerance throws exception
  def test_failsnegativetol(self):
    with self.assertRaises(AssertionError):
      ts = timeslice(self.int_fine, self.int_coarse, -1e-5, 5, self.u0fine, self.u0fine)

  # Non-float tolerance throws exception
  def test_failsintegertol(self):
    with self.assertRaises(AssertionError):
      ts = timeslice(self.int_fine, self.int_coarse, 1, 5, self.u0fine, self.u0fine)

  # Non-int iter_max raises exception
  def test_failsfloatitermax(self):
    with self.assertRaises(AssertionError):
      ts = timeslice(self.int_fine, self.int_coarse, 1e-10, 2.5, self.u0fine, self.u0fine)

  # Negative iter_max raises exception
  def test_failsnegativeitermax(self):
    with self.assertRaises(AssertionError):
      ts = timeslice(self.int_fine, self.int_coarse, 1e-10, -5, self.u0fine, self.u0fine)

  # Different values for tstart in fine and coarse integrator raise exception
  def test_failsdifferenttstart(self):
    int_c = integrator(1e-10+self.int_coarse.tstart, self.int_coarse.tend, self.int_coarse.nsteps)
    with self.assertRaises(AssertionError):
      ts = timeslice(self.int_fine, int_c, 1e-10, 5, self.u0fine, self.u0fine)

  # Different values for tend in fine and coarse integrator raise exception
  def test_failsdifferenttend(self):
    int_c = integrator(self.int_coarse.tstart, 1e-10+self.int_coarse.tend, self.int_coarse.nsteps)
    with self.assertRaises(AssertionError):
      ts = timeslice(self.int_fine, int_c, 1e-10, 5, self.u0fine, self.u0fine)

  # After running fine integrator and setting sol_end to the same value, is_converged returns True
  def test_isconverged(self):
    ts = timeslice(self.int_fine, self.int_coarse, 1e-14+np.random.rand(), 1+np.random.randint(1), self.u0fine, self.u0fine)
    sol = solution_linear(np.random.rand(self.ndof_f), np.random.rand(self.ndof_f, self.ndof_f))
    ts.set_sol_start(sol)
    ts.update_fine()
    ts.set_sol_end(ts.get_sol_fine())
    assert ts.is_converged(), "After running F and setting sol_end to the result, the residual should be zero and the time slice converged"  

  # get_tstart returns correct value
  def test_get_tstart(self):
    ts = timeslice(self.int_fine, self.int_coarse, 1e-10, 5, self.u0fine, self.u0fine)
    assert abs(ts.get_tstart() - ts.int_fine.tstart)==0, "get_start returned wrong value"

  # get_tend returns correct value
  def test_get_tend(self):
    ts = timeslice(self.int_fine, self.int_coarse, 1e-10, 5, self.u0fine, self.u0fine)
    assert abs(ts.get_tend() - ts.int_fine.tend)==0, "get_start returned wrong value"

  # set_sol_start with non-solution objects throws exception
  def test_solfinenosolutionthrows(self):
    ts = timeslice(self.int_fine, self.int_coarse, 1e-10, 5, self.u0fine, self.u0fine)
    with self.assertRaises(AssertionError):
      ts.set_sol_start(-1)

  # update_fine runs and returns value equal to what matrix provides
  def test_fineequalsmatrix(self):
    ts = timeslice(self.int_fine, self.int_coarse, 1e-10, 5, self.u0fine, self.u0fine)
    # thi
    u0 = np.random.rand(self.ndof_f)
    A  = np.random.rand(self.ndof_f, self.ndof_f)
    sol = solution_linear(u0, A)
    # NOTE: this should use the values from sol but the matrix A_f used to generate u0fine
    ts.set_sol_start(sol)
    ts.update_fine()
    sol_ts = ts.get_sol_fine()
    assert isinstance(sol_ts, solution_linear), "After running update_fine, object returned by get_sol_fine is of wrong type"
    Fmat = ts.get_fine_update_matrix(self.u0fine)
    fine = solution_linear( Fmat@u0, self.A_f)
    fine.axpy(-1.0, sol_ts)
    assert fine.norm()<1e-12, "Solution generated with get_fine_update_matrix does not match the one generated by update_fine"

  # If the length or type of the solution given to run_fine is different to what was given to the constructor, throw and exception
  def test_runfinethrowsifsolutiondifferent(self):
    pass
    
  # If the length or type of the solution given to run_coarse is different to what was given to the constructor, throw and exception
  def test_coarsefinethrowsifsolutiondifferent(self):
    pass

  # update_coarse runs and returns value equal to what matrix provides
  def test_canruncoarse(self):
    ts = timeslice(self.int_fine, self.int_coarse, 1e-10, 5, self.u0fine, self.u0fine)
    ts.update_coarse()
    sol_ts = ts.get_sol_coarse()
    assert isinstance(sol_ts, solution_linear), "After running update_coarse, object returned by get_sol_coarse is of wrong type"
    Cmat = ts.get_coarse_update_matrix(self.u0fine)
    coarse = solution_linear( Cmat@self.u0_f, self.A_f)
    coarse.axpy(-1.0, sol_ts)
    assert coarse.norm()<1e-12, "Solution generated with get_coarse_update_matrix does not match the one generated by update_coarse"
    
  # update_coarse runs and returns value equal to what matrix provides when argument u0coarse was provided
  def test_canruncoarsewithu0coarse(self):

    # create time slice and set starting solution
    ts = timeslice(self.int_fine, self.int_coarse, 1e-10, 3, self.u0fine, self.u0fine)
    ts.set_sol_start(self.u0fine)  # should not be needed
    
    # run coarse method and fetch result
    ts.update_coarse()
    sol_ts = ts.get_sol_coarse()
    
    # make sure result is again an object of type solution_linaer
    assert isinstance(sol_ts, solution_linear), "After running update_coarse, object returned by get_sol_coarse is of wrong type"
    
    # get representation of coarse propagator as matrix
    Cmat = ts.get_coarse_update_matrix(self.u0fine)
    # apply matrix
    coarse = solution_linear( Cmat@self.u0_f, self.A_f)
    coarse.axpy(-1.0, sol_ts)
    assert coarse.norm()<1e-12, "Solution generated with get_coarse_update_matrix does not match the one generated by update_coarse"
