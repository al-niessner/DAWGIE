
import dawgie.context
import dawgie.pl.state

if 'fsm' not in dir(dawgie.context): dawgie.context.fsm = dawgie.pl.state.FSM()
