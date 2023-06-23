
import dawgie.context
import dawgie.pl.state

def set_fsm(): dawgie.context.fsm = dawgie.pl.state.FSM()

if 'fsm' not in dir(dawgie.context): set_fsm()
