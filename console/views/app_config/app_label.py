# -*- coding: utf8 -*-
"""
  Created on 18/1/15.
"""
import logging
import datetime

from django.views.decorators.cache import never_cache
from rest_framework.response import Response

from console.services.app_config import label_service
from console.views.app_config.base import AppBaseView
from www.decorator import perm_required
from www.utils.return_message import general_message, error_message
from console.repositories.label_repo import label_repo, node_label_repo, service_label_repo
from www.utils.crypt import make_uuid
from www.models.label import Labels


logger = logging.getLogger("default")


class AppLabelView(AppBaseView):
    @never_cache
    @perm_required('view_service')
    def get(self, request, *args, **kwargs):
        """
        获取服务已使用和未使用的标签
        ---
        parameters:
            - name: tenantName
              description: 租户名
              required: true
              type: string
              paramType: path
            - name: serviceAlias
              description: 服务别名
              required: true
              type: string
              paramType: path

        """
        result = {}
        try:
            bean = label_service.get_service_labels(self.service)
            result = general_message(200, "success", "查询成功", bean=bean)
        except Exception as e:
            logger.exception(e)
            result = error_message(e.message)
        return Response(result, status=result["code"])

    @never_cache
    @perm_required('manage_service_config')
    def post(self, request, *args, **kwargs):
        """
        添加服务标签
        ---
        parameters:
            - name: tenantName
              description: 租户名
              required: true
              type: string
              paramType: path
            - name: serviceAlias
              description: 服务别名
              required: true
              type: string
              paramType: path
            - name: body
              description: 服务标签 ["label_id1","label_id2"]
              required: true
              type: string
              paramType: body
        """
        result = {}
        try:
            label_ids = request.data.get("label_ids", None)
            if not label_ids:
                return Response(general_message(400, "param error", "标签ID未指定"), status=400)

            code, msg, event = label_service.add_service_labels(self.tenant, self.service, label_ids)
            if code != 200:
                return Response(general_message(code, "add labels error", msg), status=code)
            result = general_message(200, "success", "标签添加成功")
        except Exception as e:
            logger.exception(e)
            result = error_message(e.message)
        return Response(result, status=result["code"])

    @never_cache
    @perm_required('manage_service_config')
    def delete(self, request, *args, **kwargs):
        """
        删除服务标签
        ---
        parameters:
            - name: tenantName
              description: 租户名
              required: true
              type: string
              paramType: path
            - name: serviceAlias
              description: 服务别名
              required: true
              type: string
              paramType: path
            - name: label_id
              description: 服务标签 id
              required: true
              type: string
              paramType: form
        """
        result = {}
        try:
            label_id = request.data.get("label_id", None)
            if not label_id:
                return Response(general_message(400, "param error", "标签ID未指定"), status=400)

            code, msg, event = label_service.delete_service_label(self.tenant, self.service, label_id)
            if code != 200:
                return Response(general_message(code, "add labels error", msg), status=code)
            result = general_message(200, "success", "标签删除成功")
        except Exception as e:
            logger.exception(e)
            result = error_message(e.message)
        return Response(result, status=result["code"])


# 添加特性获取可用标签
class AppLabelAvailableView(AppBaseView):
    @never_cache
    @perm_required('view_service')
    def get(self, request, *args, **kwargs):
        """
        添加特性获取可用标签
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            labels = label_repo.get_all_labels()
            if labels:
                labels_name_list = [label.label_name for label in labels]
                if "windows" not in labels_name_list:
                    label_id = make_uuid("windows")
                    create_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    label = Labels(label_id=label_id, label_name="windows", label_alias="windows", create_time=create_time)
                    label.save()
            else:
                label_id = make_uuid("windows")
                create_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                label = Labels(label_id=label_id, label_name="windows", label_alias="windows", create_time=create_time)
                label.save()
            # 节点添加的标签和windows标签才可被服务使用
            node_labels = node_label_repo.get_all_labels()
            labels_list = list()
            if node_labels:
                node_labels_id_list = [label.label_id for label in node_labels]
                label_obj_list = label_repo.get_labels_by_label_ids(node_labels_id_list)
                labels_name_list = [label.label_name for label in label_obj_list]
                if "windows" not in labels_name_list:
                    labels_name_list.append("windows")
                service_labels = service_label_repo.get_service_labels(self.service.service_id)
                if service_labels:
                    service_labels_id_list = [label.label_id for label in service_labels]
                    label_obj_list = label_repo.get_labels_by_label_ids(service_labels_id_list)
                    service_labels_name_list = [label.label_name for label in label_obj_list]
                    for service_labels_name in service_labels_name_list:
                        if service_labels_name in labels_name_list:
                            labels_name_list.remove(service_labels_name)
                for labels_name in labels_name_list:
                    label_dict = dict()
                    label_oj = label_repo.get_labels_by_label_name(labels_name)
                    label_dict["label_id"] = label_oj.label_id
                    label_dict["label_alias"] = label_oj.label_alias
                    labels_list.append(label_dict)
            result = general_message(200, "success", "查询成功", list=labels_list)
        except Exception as e:
            logger.exception(e)
            result = error_message(e.message)
        return Response(result, status=result["code"])


