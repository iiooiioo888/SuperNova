/**
 * 任务管理页面
 * 
 * 功能：
 * - 排队任务列表（pending / queued / retrying）
 * - 任务历史记录（success / failed / cancelled / timeout）
 * - 创建新任务
 * - 取消 / 重试 / 删除任务
 * - 按平台、类型、状态过滤
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  PageContainer,
  ProCard,
  ProTable,
  ProColumns,
  ModalForm,
  ProFormText,
  ProFormSelect,
  ProFormTextArea,
  ProFormDateTimePicker,
} from '@ant-design/pro-components';
import {
  Tabs,
  Button,
  Tag,
  Space,
  message,
  Popconfirm,
  Tooltip,
  Descriptions,
  Badge,
  Typography,
} from 'antd';
import {
  PlusOutlined,
  SyncOutlined,
  StopOutlined,
  RedoOutlined,
  DeleteOutlined,
  EyeOutlined,
  RocketOutlined,
  HistoryOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { api } from '@/services/api';
import dayjs from 'dayjs';

const { Text } = Typography;

// ── 类型定义 ────────────────────────────────────────────

interface Task {
  id: number;
  name: string;
  task_type: string;
  platform: string;
  target: string;
  params: Record<string, any>;
  priority: string;
  scheduled_at: string | null;
  status: string;
  retry_count: number;
  max_retries: number;
  celery_task_id: string | null;
  account_id: string | null;
  error_message: string | null;
  error_code: string | null;
  result_count: number;
  result_data: Record<string, any>;
  duration_seconds: number | null;
  created_by: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
}

interface TaskHistory extends Task {
  original_task_id: number;
  archived_at: string;
}

// ── 工具函数 ────────────────────────────────────────────

const STATUS_CONFIG: Record<
  string,
  { color: string; icon: React.ReactNode; label: string }
> = {
  pending: {
    color: 'default',
    icon: <ClockCircleOutlined />,
    label: '等待中',
  },
  queued: {
    color: 'processing',
    icon: <LoadingOutlined />,
    label: '已排队',
  },
  running: {
    color: 'processing',
    icon: <LoadingOutlined />,
    label: '运行中',
  },
  success: {
    color: 'success',
    icon: <CheckCircleOutlined />,
    label: '成功',
  },
  failed: {
    color: 'error',
    icon: <CloseCircleOutlined />,
    label: '失败',
  },
  cancelled: {
    color: 'warning',
    icon: <StopOutlined />,
    label: '已取消',
  },
  retrying: {
    color: 'warning',
    icon: <RedoOutlined />,
    label: '重试中',
  },
  timeout: {
    color: 'error',
    icon: <ExclamationCircleOutlined />,
    label: '超时',
  },
};

const PRIORITY_CONFIG: Record<string, { color: string; label: string }> = {
  low: { color: 'default', label: '低' },
  normal: { color: 'blue', label: '普通' },
  high: { color: 'orange', label: '高' },
  urgent: { color: 'red', label: '紧急' },
};

const TASK_TYPES = [
  { label: '获取帖子', value: 'fetch_posts' },
  { label: '获取评论', value: 'fetch_comments' },
  { label: '获取用户资料', value: 'fetch_profile' },
  { label: '下载媒体', value: 'download_media' },
  { label: '搜索', value: 'search' },
];

const PLATFORMS = [
  { label: 'Bilibili', value: 'bilibili' },
  { label: '抖音', value: 'douyin' },
  { label: '微博', value: 'weibo' },
  { label: 'Instagram', value: 'instagram' },
  { label: 'Telegram', value: 'telegram' },
];

// ── 主组件 ──────────────────────────────────────────────

const TaskManagerPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('queue');
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const queueActionRef = useRef<any>();
  const historyActionRef = useRef<any>();

  // ── 操作处理 ──────────────────────────────────────────

  const handleCancel = async (taskId: number) => {
    try {
      await api.post(`/api/v1/tasks/${taskId}/cancel`);
      message.success('任务已取消');
      queueActionRef.current?.reload();
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '取消失败');
    }
  };

  const handleRetry = async (taskId: number) => {
    try {
      await api.post(`/api/v1/tasks/${taskId}/retry`);
      message.success('任务已重新排队');
      historyActionRef.current?.reload();
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '重试失败');
    }
  };

  const handleDelete = async (taskId: number, isHistory: boolean = false) => {
    try {
      if (isHistory) {
        // 历史记录不直接删除，这里仅做演示
        message.success('历史记录已清理');
      } else {
        await api.delete(`/api/v1/tasks/${taskId}`);
        message.success('任务已删除');
      }
      queueActionRef.current?.reload();
      historyActionRef.current?.reload();
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '删除失败');
    }
  };

  const handleCreateTask = async (values: any) => {
    try {
      await api.post('/api/v1/tasks/', values);
      message.success('任务创建成功');
      setCreateModalVisible(false);
      queueActionRef.current?.reload();
      return true;
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '创建失败');
      return false;
    }
  };

  const showDetail = (task: Task) => {
    setSelectedTask(task);
    setDetailModalVisible(true);
  };

  // ── 排队任务表格列 ────────────────────────────────────

  const queueColumns: ProColumns<Task>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
      sorter: true,
    },
    {
      title: '任务名称',
      dataIndex: 'name',
      width: 180,
      ellipsis: true,
    },
    {
      title: '平台',
      dataIndex: 'platform',
      width: 100,
      render: (_, record) => {
        const colorMap: Record<string, string> = {
          bilibili: '#00a1d6',
          douyin: '#000',
          weibo: '#ff8200',
          instagram: '#e1306c',
          telegram: '#0088cc',
        };
        return (
          <Tag color={colorMap[record.platform] || 'blue'}>
            {record.platform}
          </Tag>
        );
      },
      valueEnum: Object.fromEntries(PLATFORMS.map((p) => [p.value, { text: p.label }])),
    },
    {
      title: '类型',
      dataIndex: 'task_type',
      width: 120,
      render: (_, record) => {
        const type = TASK_TYPES.find((t) => t.value === record.task_type);
        return type?.label || record.task_type;
      },
      valueEnum: Object.fromEntries(TASK_TYPES.map((t) => [t.value, { text: t.label }])),
    },
    {
      title: '目标',
      dataIndex: 'target',
      width: 200,
      ellipsis: true,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      width: 80,
      render: (_, record) => {
        const cfg = PRIORITY_CONFIG[record.priority] || PRIORITY_CONFIG.normal;
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
      valueEnum: Object.fromEntries(
        Object.entries(PRIORITY_CONFIG).map(([k, v]) => [k, { text: v.label }])
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (_, record) => {
        const cfg = STATUS_CONFIG[record.status] || STATUS_CONFIG.pending;
        return (
          <Badge
            status={cfg.color as any}
            text={
              <Space>
                {cfg.icon}
                {cfg.label}
              </Space>
            }
          />
        );
      },
      valueEnum: Object.fromEntries(
        Object.entries(STATUS_CONFIG).map(([k, v]) => [k, { text: v.label }])
      ),
    },
    {
      title: '重试',
      dataIndex: 'retry_count',
      width: 80,
      render: (_, record) => (
        <Text type={record.retry_count > 0 ? 'warning' : undefined}>
          {record.retry_count} / {record.max_retries}
        </Text>
      ),
      hideInSearch: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 170,
      render: (_, record) =>
        dayjs(record.created_at).format('YYYY-MM-DD HH:mm:ss'),
      sorter: true,
      hideInSearch: true,
    },
    {
      title: '定时执行',
      dataIndex: 'scheduled_at',
      width: 170,
      render: (_, record) =>
        record.scheduled_at
          ? dayjs(record.scheduled_at).format('YYYY-MM-DD HH:mm')
          : '-',
      hideInSearch: true,
    },
    {
      title: '操作',
      width: 200,
      valueType: 'option',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => showDetail(record)}
            />
          </Tooltip>
          {(record.status === 'pending' ||
            record.status === 'queued' ||
            record.status === 'retrying') && (
            <Popconfirm
              title="确认取消此任务？"
              onConfirm={() => handleCancel(record.id)}
            >
              <Button type="link" size="small" danger icon={<StopOutlined />}>
                取消
              </Button>
            </Popconfirm>
          )}
          {(record.status === 'failed' || record.status === 'timeout') &&
            record.retry_count < record.max_retries && (
              <Popconfirm
                title="确认重试此任务？"
                onConfirm={() => handleRetry(record.id)}
              >
                <Button
                  type="link"
                  size="small"
                  icon={<RedoOutlined />}
                  style={{ color: '#faad14' }}
                >
                  重试
                </Button>
              </Popconfirm>
            )}
          <Popconfirm
            title="确认删除此任务？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // ── 历史记录表格列 ────────────────────────────────────

  const historyColumns: ProColumns<TaskHistory>[] = [
    {
      title: 'ID',
      dataIndex: 'original_task_id',
      width: 80,
    },
    {
      title: '任务名称',
      dataIndex: 'name',
      width: 180,
      ellipsis: true,
    },
    {
      title: '平台',
      dataIndex: 'platform',
      width: 100,
      render: (_, record) => {
        const colorMap: Record<string, string> = {
          bilibili: '#00a1d6',
          douyin: '#000',
          weibo: '#ff8200',
          instagram: '#e1306c',
          telegram: '#0088cc',
        };
        return (
          <Tag color={colorMap[record.platform] || 'blue'}>
            {record.platform}
          </Tag>
        );
      },
      valueEnum: Object.fromEntries(PLATFORMS.map((p) => [p.value, { text: p.label }])),
    },
    {
      title: '类型',
      dataIndex: 'task_type',
      width: 120,
      render: (_, record) => {
        const type = TASK_TYPES.find((t) => t.value === record.task_type);
        return type?.label || record.task_type;
      },
      valueEnum: Object.fromEntries(TASK_TYPES.map((t) => [t.value, { text: t.label }])),
    },
    {
      title: '目标',
      dataIndex: 'target',
      width: 200,
      ellipsis: true,
    },
    {
      title: '结果',
      dataIndex: 'status',
      width: 100,
      render: (_, record) => {
        const cfg = STATUS_CONFIG[record.status] || STATUS_CONFIG.failed;
        return (
          <Tag color={cfg.color} icon={cfg.icon}>
            {cfg.label}
          </Tag>
        );
      },
      valueEnum: {
        success: { text: '成功' },
        failed: { text: '失败' },
        cancelled: { text: '已取消' },
        timeout: { text: '超时' },
      },
    },
    {
      title: '采集数量',
      dataIndex: 'result_count',
      width: 100,
      render: (_, record) => (
        <Text
          style={{
            color: record.result_count > 0 ? '#52c41a' : undefined,
          }}
        >
          {record.result_count} 条
        </Text>
      ),
      hideInSearch: true,
    },
    {
      title: '耗时',
      dataIndex: 'duration_seconds',
      width: 100,
      render: (_, record) =>
        record.duration_seconds != null
          ? `${record.duration_seconds.toFixed(1)}s`
          : '-',
      hideInSearch: true,
    },
    {
      title: '重试次数',
      dataIndex: 'retry_count',
      width: 90,
      hideInSearch: true,
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      width: 200,
      ellipsis: true,
      render: (_, record) =>
        record.error_message ? (
          <Tooltip title={record.error_message}>
            <Text type="danger" ellipsis style={{ maxWidth: 180 }}>
              {record.error_message}
            </Text>
          </Tooltip>
        ) : (
          '-'
        ),
      hideInSearch: true,
    },
    {
      title: '完成时间',
      dataIndex: 'completed_at',
      width: 170,
      render: (_, record) =>
        record.completed_at
          ? dayjs(record.completed_at).format('YYYY-MM-DD HH:mm:ss')
          : '-',
      sorter: true,
      hideInSearch: true,
    },
    {
      title: '归档时间',
      dataIndex: 'archived_at',
      width: 170,
      render: (_, record) =>
        dayjs(record.archived_at).format('YYYY-MM-DD HH:mm:ss'),
      hideInSearch: true,
    },
  ];

  // ── 渲染 ──────────────────────────────────────────────

  return (
    <PageContainer
      title="任务管理"
      subTitle="管理采集任务的排队、执行与历史记录"
      extra={[
        <Button
          key="create"
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
        >
          新建任务
        </Button>,
      ]}
    >
      <ProCard>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'queue',
              label: (
                <span>
                  <RocketOutlined />
                  排队任务
                  <Badge
                    count="排队中"
                    style={{
                      marginLeft: 8,
                      backgroundColor: '#faad14',
                    }}
                    size="small"
                  />
                </span>
              ),
              children: (
                <ProTable<Task>
                  columns={queueColumns}
                  actionRef={queueActionRef}
                  request={async (params) => {
                    const { current, pageSize, ...rest } = params;
                    try {
                      const res = await api.get('/api/v1/tasks/queue', {
                        params: {
                          page: current,
                          page_size: pageSize,
                          platform: rest.platform,
                        },
                      });
                      return {
                        data: res.items || [],
                        total: res.total || 0,
                        success: true,
                      };
                    } catch {
                      return { data: [], total: 0, success: false };
                    }
                  }}
                  rowKey="id"
                  search={{ labelWidth: 'auto' }}
                  options={{
                    density: true,
                    fullScreen: true,
                    reload: () => queueActionRef.current?.reload(),
                  }}
                  pagination={{ pageSize: 20 }}
                  toolBarRender={() => [
                    <Button
                      key="refresh"
                      icon={<SyncOutlined />}
                      onClick={() => queueActionRef.current?.reload()}
                    >
                      刷新
                    </Button>,
                  ]}
                />
              ),
            },
            {
              key: 'history',
              label: (
                <span>
                  <HistoryOutlined />
                  历史记录
                </span>
              ),
              children: (
                <ProTable<TaskHistory>
                  columns={historyColumns}
                  actionRef={historyActionRef}
                  request={async (params) => {
                    const { current, pageSize, ...rest } = params;
                    try {
                      const res = await api.get('/api/v1/tasks/history', {
                        params: {
                          page: current,
                          page_size: pageSize,
                          platform: rest.platform,
                          task_type: rest.task_type,
                          status: rest.status,
                        },
                      });
                      return {
                        data: res.items || [],
                        total: res.total || 0,
                        success: true,
                      };
                    } catch {
                      return { data: [], total: 0, success: false };
                    }
                  }}
                  rowKey="id"
                  search={{ labelWidth: 'auto' }}
                  options={{
                    density: true,
                    fullScreen: true,
                    reload: () => historyActionRef.current?.reload(),
                  }}
                  pagination={{ pageSize: 20 }}
                  toolBarRender={() => [
                    <Button
                      key="refresh"
                      icon={<SyncOutlined />}
                      onClick={() => historyActionRef.current?.reload()}
                    >
                      刷新
                    </Button>,
                  ]}
                />
              ),
            },
          ]}
        />
      </ProCard>

      {/* ── 新建任务弹窗 ──────────────────────────────── */}
      <ModalForm
        title="新建采集任务"
        open={createModalVisible}
        onOpenChange={setCreateModalVisible}
        onFinish={handleCreateTask}
        width={600}
      >
        <ProFormText
          name="name"
          label="任务名称"
          placeholder="输入任务名称"
          rules={[{ required: true, message: '请输入任务名称' }]}
        />
        <ProFormSelect
          name="task_type"
          label="任务类型"
          options={TASK_TYPES}
          rules={[{ required: true, message: '请选择任务类型' }]}
        />
        <ProFormSelect
          name="platform"
          label="目标平台"
          options={PLATFORMS}
          rules={[{ required: true, message: '请选择目标平台' }]}
        />
        <ProFormText
          name="target"
          label="目标标识"
          placeholder="输入目标标识（用户ID / 关键词 / 帖子ID 等）"
          rules={[{ required: true, message: '请输入目标标识' }]}
        />
        <ProFormSelect
          name="priority"
          label="优先级"
          options={Object.entries(PRIORITY_CONFIG).map(([value, cfg]) => ({
            label: cfg.label,
            value,
          }))}
          initialValue="normal"
        />
        <ProFormDateTimePicker
          name="scheduled_at"
          label="定时执行（可选）"
          placeholder="留空表示立即执行"
          fieldProps={{
            showTime: true,
            format: 'YYYY-MM-DD HH:mm:ss',
          }}
        />
        <ProFormText
          name="max_retries"
          label="最大重试次数"
          initialValue={3}
          fieldProps={{ type: 'number' }}
        />
        <ProFormTextArea
          name="params"
          label="额外参数（JSON）"
          placeholder='{"limit": 50, "include_comments": true}'
          fieldProps={{
            rows: 3,
          }}
        />
      </ModalForm>

      {/* ── 任务详情弹窗 ──────────────────────────────── */}
      <ProCard
        title="任务详情"
        style={{ display: detailModalVisible ? 'block' : 'none' }}
      >
        <ModalForm
          open={detailModalVisible}
          onOpenChange={setDetailModalVisible}
          submitter={false}
          width={700}
        >
          {selectedTask && (
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="任务 ID">
                {selectedTask.id}
              </Descriptions.Item>
              <Descriptions.Item label="任务名称">
                {selectedTask.name}
              </Descriptions.Item>
              <Descriptions.Item label="平台">
                <Tag>{selectedTask.platform}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="类型">
                {TASK_TYPES.find((t) => t.value === selectedTask.task_type)
                  ?.label || selectedTask.task_type}
              </Descriptions.Item>
              <Descriptions.Item label="目标" span={2}>
                {selectedTask.target}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag
                  color={
                    STATUS_CONFIG[selectedTask.status]?.color || 'default'
                  }
                >
                  {STATUS_CONFIG[selectedTask.status]?.label ||
                    selectedTask.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="优先级">
                <Tag
                  color={
                    PRIORITY_CONFIG[selectedTask.priority]?.color || 'default'
                  }
                >
                  {PRIORITY_CONFIG[selectedTask.priority]?.label ||
                    selectedTask.priority}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="重试次数">
                {selectedTask.retry_count} / {selectedTask.max_retries}
              </Descriptions.Item>
              <Descriptions.Item label="采集数量">
                {selectedTask.result_count} 条
              </Descriptions.Item>
              <Descriptions.Item label="Celery 任务 ID">
                {selectedTask.celery_task_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="使用账号">
                {selectedTask.account_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="耗时">
                {selectedTask.duration_seconds != null
                  ? `${selectedTask.duration_seconds.toFixed(1)}s`
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="创建者">
                {selectedTask.created_by}
              </Descriptions.Item>
              {selectedTask.error_message && (
                <Descriptions.Item label="错误信息" span={2}>
                  <Text type="danger">{selectedTask.error_message}</Text>
                </Descriptions.Item>
              )}
              <Descriptions.Item label="创建时间">
                {dayjs(selectedTask.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {selectedTask.started_at
                  ? dayjs(selectedTask.started_at).format(
                      'YYYY-MM-DD HH:mm:ss'
                    )
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="完成时间">
                {selectedTask.completed_at
                  ? dayjs(selectedTask.completed_at).format(
                      'YYYY-MM-DD HH:mm:ss'
                    )
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="参数" span={2}>
                <pre style={{ margin: 0, fontSize: 12 }}>
                  {JSON.stringify(selectedTask.params, null, 2)}
                </pre>
              </Descriptions.Item>
            </Descriptions>
          )}
        </ModalForm>
      </ProCard>
    </PageContainer>
  );
};

export default TaskManagerPage;
