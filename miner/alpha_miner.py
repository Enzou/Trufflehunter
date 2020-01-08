from typing import Tuple

from pm4py.objects.petri.petrinet import Marking, PetriNet
from pm4py.algo.discovery.alpha import factory as alpha_miner
from pm4py.util.constants import PARAMETER_CONSTANT_CASEID_KEY, PARAMETER_CONSTANT_ACTIVITY_KEY

from src.event_log.eventlog import EventLog


class AlphaMiner:

    def mine(self, log: EventLog) -> Tuple[PetriNet, Marking, Marking]:
        params = {
            PARAMETER_CONSTANT_CASEID_KEY: log.case_id_attr,
            PARAMETER_CONSTANT_ACTIVITY_KEY: log.activity_attr
        }

        res_tpl = alpha_miner.apply(log, parameters=params)
        return res_tpl
