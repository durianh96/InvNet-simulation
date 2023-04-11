from typing import Union
from math import ceil
import numpy as np


class EvaNode:
    def __init__(self, node_id: str, lt: Union[int, float],
                 sim_steps_num: int, decision_time_steps: list, sim_unit: Union[int, float]):
        # node properties
        self.node_id = node_id
        self.lt = lt

        # simulation time info
        self.time_step = 0
        self.sim_steps_num = sim_steps_num
        self.decision_time_steps = decision_time_steps
        self.sim_unit = sim_unit

        # node inventory status
        self.on_hand = 0.
        self.inv_pos = 0.
        self.backorder = 0.
        self.working_inv = {i: 0. for i in range(self.sim_steps_num)}

        self.records = {
            'on_hand_begin': [],
            'inv_pos_begin': [],
            'backorder_begin': [],
            'working_inv_sum_begin': [],
            'on_hand_end': [],
            'inv_pos_end': [],
            'backorder_end': [],
            'working_inv_sum_end': [],
            'fill_qty': [],
            'plan_qty': [],
            'demand_sample': []
        }


def record_begin_inv_status(sn: EvaNode):
    sn.records['on_hand_begin'].append((sn.time_step, sn.on_hand))
    sn.records['inv_pos_begin'].append((sn.time_step, sn.inv_pos))
    sn.records['backorder_begin'].append((sn.time_step, sn.backorder))
    sn.records['working_inv_sum_begin'].append((sn.time_step, sum(sn.working_inv.values())))


def record_end_inv_status(sn: EvaNode):
    sn.records['on_hand_end'].append((sn.time_step, sn.on_hand))
    sn.records['inv_pos_end'].append((sn.time_step, sn.inv_pos))
    sn.records['backorder_end'].append((sn.time_step, sn.backorder))
    sn.records['working_inv_sum_end'].append((sn.time_step, sum(sn.working_inv.values())))


def receive_working_inv(sn: EvaNode):
    sn.on_hand += sn.working_inv[sn.time_step]
    sn.working_inv[sn.time_step] = 0.


def fulfill_external_demand_backorder(sn: EvaNode, ds: float):
    sn.records['demand_sample'].append((sn.time_step, ds))

    fill_qty = min(sn.on_hand, sn.backorder + ds)
    sn.records['fill_qty'].append((sn.time_step, 'ext', fill_qty))

    sn.on_hand -= fill_qty
    sn.backorder = sn.backorder + ds - fill_qty
    sn.inv_pos -= ds


def fulfill_external_demand_lostsales(sn: EvaNode, ds: float):
    sn.records['demand_sample'].append((sn.time_step, ds))

    fill_qty = min(sn.on_hand, ds)
    sn.records['fill_qty'].append((sn.time_step, 'ext', fill_qty))

    sn.on_hand -= fill_qty
    sn.inv_pos -= fill_qty


def fulfill_succ_demand(sn: EvaNode, succ_id: str, fill_succ_qty: float):
    sn.records['fill_qty'].append((sn.time_step, succ_id, fill_succ_qty))


def review_inv_pos(sn: EvaNode):
    inv_pos = sn.on_hand + sum(sn.working_inv.values()) - sn.backorder
    return inv_pos


def update_inv_pos(sn: EvaNode, new_inv_pos):
    sn.inv_pos = new_inv_pos


def update_plan_qty(sn: EvaNode, new_plan_qty):
    sn.records['plan_qty'].append((sn.time_step, new_plan_qty))
    sn.inv_pos += new_plan_qty
    receive_time_step = sn.time_step + ceil(sn.lt / sn.sim_unit)
    if receive_time_step < sn.sim_steps_num:
        sn.working_inv[receive_time_step] += new_plan_qty


def skip_plan(sn: EvaNode):
    sn.records['plan_qty'].append((sn.time_step, np.nan))
