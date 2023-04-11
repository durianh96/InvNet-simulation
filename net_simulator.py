from sim_node import *
from default_sim_paras import *

from typing import Optional
from sim_utils import *
from graph_algorithms import cal_lt_of_node, find_preds_of_node, find_succs_of_node


class NetEvaluator:
    def __init__(self, nodes: set, edges: list, edge_qty: dict, process_lt_of_node: dict, lt_of_edge: dict,
                 oul_of_node: dict, priority_sort: Optional[list] = None,
                 rop_of_node: Optional[dict] = None,
                 review_cycle_of_node: Optional[dict] = None,
                 sim_steps_num: int = DEFAULT_SIM_STEPS_NUM,
                 sim_unit: int = DEFAULT_SIM_UNIT,
                 backorder: bool = True,
                 priority: bool = True):

        self.nodes = nodes
        self.edges = edges
        self.supply_nodes = set([i for i, _ in edges]) - set([j for _, j in edges])
        self.demand_nodes = set([j for _, j in edges]) - set([i for i, _ in edges])
        self.preds_of_node = find_preds_of_node(edges)
        self.succs_of_node = find_succs_of_node(edges)
        self.edge_qty = edge_qty

        self.process_lt_of_node = process_lt_of_node
        self.lt_of_edge = lt_of_edge

        if priority and priority_sort is None:
            raise AttributeError("Priority is True, but priority_sort is None.")
        self.priority = priority
        self.priority_sort = priority_sort

        self.oul_of_node = oul_of_node
        self.rop_of_node = {}
        self.review_cycle_of_node = {}

        if rop_of_node is None:
            rop_of_node = {}
        if review_cycle_of_node is None:
            review_cycle_of_node = {}
        for n_id in nodes:
            if n_id not in rop_of_node or rop_of_node[n_id] is None:
                self.rop_of_node[n_id] = oul_of_node[n_id]

            if n_id not in review_cycle_of_node or review_cycle_of_node[n_id] is None:
                self.review_cycle_of_node[n_id] = DEFAULT_REVIEW_CYCLE
            else:
                self.review_cycle_of_node[n_id] = review_cycle_of_node[n_id]

        self.external_demand_samples_node = {}

        self.sim_steps_num = sim_steps_num
        self.sim_unit = sim_unit
        self.backorder = backorder

        self.sim_nodes_pool = {}

    def run(self):
        self.sim_nodes_pool_init()
        for t in range(self.sim_steps_num):
            self.sim_one_step()

    def sim_one_step(self):
        self.all_nodes_receive_working_inv()
        self.all_nodes_record_begin_inv_status()
        self.all_external_demand_fulfill()
        if self.priority:
            self.all_nodes_make_plan_by_priority()
        else:
            self.all_nodes_make_plan_by_avg()
        self.all_nodes_record_end_inv_status()
        self.all_nodes_take_next_step()

    def sim_nodes_pool_init(self):
        time_index = list(range(self.sim_steps_num))
        lt_of_node = cal_lt_of_node(self.edges, self.process_lt_of_node, self.lt_of_edge)

        for n_id in self.nodes:
            n_decision_time_steps = [i for i, t in enumerate(time_index)
                                     if (t % self.review_cycle_of_node[n_id] == 0) and (t > 0)]

            self.sim_nodes_pool[n_id] = EvaNode(n_id, lt_of_node[n_id], self.sim_steps_num, n_decision_time_steps,
                                                self.sim_unit)

            if n_id in self.demand_nodes:
                self.external_demand_samples_node[n_id] = normal_ds_generating(sample_size=self.sim_steps_num)

    def all_nodes_receive_working_inv(self):
        for n_id in self.nodes:
            receive_working_inv(self.sim_nodes_pool[n_id])

    def all_nodes_record_begin_inv_status(self):
        for n_id in self.nodes:
            record_begin_inv_status(self.sim_nodes_pool[n_id])

    def all_external_demand_fulfill(self):
        for n_id in self.demand_nodes:
            n_ds = self.external_demand_samples_node[n_id][self.sim_nodes_pool[n_id].time_step]
            if self.backorder:
                fulfill_external_demand_backorder(self.sim_nodes_pool[n_id], n_ds)
            else:
                fulfill_external_demand_lostsales(self.sim_nodes_pool[n_id], n_ds)

    def all_nodes_make_plan_by_priority(self):
        to_plan_nodes = [n_id for n_id in self.nodes
                         if (self.sim_nodes_pool[n_id].time_step in self.sim_nodes_pool[n_id].decision_time_steps) and (
                                 self.sim_nodes_pool[n_id].inv_pos < self.rop_of_node[n_id])]
        for n_id in self.priority_sort:
            if n_id in to_plan_nodes:
                if n_id not in self.supply_nodes:
                    max_supply_qty = min([self.sim_nodes_pool[pred].on_hand / self.edge_qty[(pred, n_id)]
                                          for pred in self.preds_of_node[n_id]])
                    plan_qty = min(max_supply_qty, self.oul_of_node[n_id] - self.sim_nodes_pool[n_id].inv_pos)
                    update_plan_qty(self.sim_nodes_pool[n_id], plan_qty)
                    for pred in self.preds_of_node[n_id]:
                        pred_fill_qty = self.edge_qty[pred, n_id] * plan_qty
                        fulfill_succ_demand(self.sim_nodes_pool[pred], n_id, pred_fill_qty)
                else:
                    plan_qty = self.oul_of_node[n_id] - self.sim_nodes_pool[n_id].inv_pos
                    update_plan_qty(self.sim_nodes_pool[n_id], plan_qty)
                    skip_plan(self.sim_nodes_pool[n_id])
            else:
                skip_plan(self.sim_nodes_pool[n_id])

    def all_nodes_make_plan_by_avg(self):
        internal_rate = {n_id: 1 for n_id in self.nodes - self.demand_nodes}
        to_plan_nodes = [n_id for n_id in self.nodes
                         if (self.sim_nodes_pool[n_id].time_step in self.sim_nodes_pool[n_id].decision_time_steps) and (
                                 self.sim_nodes_pool[n_id].inv_pos < self.rop_of_node[n_id])]
        for n_id in self.nodes - self.demand_nodes:
            sum_succ_requests = sum([self.edge_qty[n_id, succ]
                                     * (self.oul_of_node[succ] - self.sim_nodes_pool[n_id].inv_pos)
                                     for succ in self.succs_of_node[n_id] if succ in to_plan_nodes])
            if sum_succ_requests > 0:
                internal_rate[n_id] = min(self.sim_nodes_pool[n_id].on_hand / sum_succ_requests, 1)

        for n_id in self.nodes:
            if n_id in to_plan_nodes:
                if n_id not in self.supply_nodes:
                    plan_qty = min([internal_rate[pred] for pred in self.preds_of_node[n_id]]) \
                               * (self.oul_of_node[n_id] - self.sim_nodes_pool[n_id].inv_pos)
                    update_plan_qty(self.sim_nodes_pool[n_id], plan_qty)
                    for pred in self.preds_of_node[n_id]:
                        pred_fill_qty = self.edge_qty[pred, n_id] * plan_qty
                        fulfill_succ_demand(self.sim_nodes_pool[pred], n_id, pred_fill_qty)
                else:
                    plan_qty = self.oul_of_node[n_id] - self.sim_nodes_pool[n_id].inv_pos
                    update_plan_qty(self.sim_nodes_pool[n_id], plan_qty)
                    skip_plan(self.sim_nodes_pool[n_id])
            else:
                skip_plan(self.sim_nodes_pool[n_id])

    def all_nodes_record_end_inv_status(self):
        for n_id in self.nodes:
            record_end_inv_status(self.sim_nodes_pool[n_id])

    def all_nodes_take_next_step(self):
        for n_id in self.nodes:
            self.sim_nodes_pool[n_id].time_step += 1
