class integrator:

  def __init__(self, tstart, tend, nsteps):
    assert tstart<tend, "tstart must be smaller than tend"
    assert (isinstance(nsteps, int) and nsteps>0), "nsteps must be a positive integer"
    self.tstart = tstart
    self.tend   = tend
    self.nsteps = nsteps
    self.dt     = (tend - tstart)/float(nsteps)

  # Run integrator from tstart to tend using nstep many steps
  def run(self):
    raise valueError("run function in generic integrator not implemented")