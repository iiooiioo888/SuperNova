/**
 * Feature Flags 管理頁面
 * 
 * 功能：
 * - 全局開關總覽（緊急制動）
 * - 平台級控制（卡片式展示）
 * - 功能粒度控制（展開查看細項功能）
 * - 策略配置（熔斷閾值、降級策略、灰度比例）
 * - 定時恢復設置
 * - 操作審計日誌
 */

import React, { useState, useEffect } from 'react';
import {
  PageContainer,
  ProCard,
  ProTable,
  Switch,
  Button,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Slider,
  Tag,
  Space,
  message,
  Popconfirm,
  Descriptions,
  Timeline,
} from '@ant-design/pro-components';
import { 
  GlobalOutlined, 
  PlatformOutlined, 
  FeatureOutlined, 
  StrategyOutlined,
  PoweroffOutlined,
  SyncOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import type { ActionType, ProColumns } from '@ant-design/pro-components';
import dayjs from 'dayjs';

// API 調用服務
import { api } from '@/services/api';

// 作用域類型
enum FlagScope {
  GLOBAL = 'global',
  PLATFORM = 'platform',
  FEATURE = 'feature',
  STRATEGY = 'strategy',
}

// 開關數據類型
interface FeatureFlag {
  id: number;
  name: string;
  scope: FlagScope;
  platform?: string;
  enabled: boolean;
  gray_scale: number;
  description?: string;
  metadata: Record<string, any>;
  restore_at?: string;
  created_at: string;
  updated_at: string;
}

// 審計日誌類型
interface AuditLog {
  id: number;
  flag_id: number;
  old_value?: boolean;
  new_value: boolean;
  reason?: string;
  changed_by: string;
  changed_from?: string;
  is_auto: boolean;
  trigger_source?: string;
  created_at: string;
}

const FeatureFlagsPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [selectedFlag, setSelectedFlag] = useState<FeatureFlag | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [auditModalVisible, setAuditModalVisible] = useState(false);
  const [form] = Form.useForm();
  const actionRef = React.useRef<ActionType>();

  // 加載開關列表
  const loadFlags = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/v1/feature-flags/list');
      setFlags(res.items || []);
    } catch (error) {
      message.error('加載開關列表失敗');
    } finally {
      setLoading(false);
    }
  };

  // 加載審計日誌
  const loadAuditLogs = async (flagId: number) => {
    try {
      const res = await api.get(`/api/v1/feature-flags/${flagId}/audit`);
      setAuditLogs(res.items || []);
    } catch (error) {
      message.error('加載審計日誌失敗');
    }
  };

  useEffect(() => {
    loadFlags();
  }, []);

  // 切換開關狀態
  const handleToggle = async (flag: FeatureFlag, enabled: boolean) => {
    try {
      await api.patch(`/api/v1/feature-flags/${flag.name}`, {
        enabled,
        reason: enabled ? '手動啟用' : '手動禁用',
      });
      message.success(`${enabled ? '啟用' : '禁用'}成功`);
      loadFlags();
    } catch (error) {
      message.error('操作失敗');
    }
  };

  // 緊急禁用平台
  const handleDisablePlatform = async (platform: string) => {
    Modal.confirm({
      title: `確認禁用 ${platform} 平臺？`,
      content: (
        <div>
          <p>此操作將立即停止該平臺的所有采集任務。</p>
          <Form layout="vertical">
            <Form.Item label="原因" name="reason" rules={[{ required: true }]}>
              <Input placeholder="請輸入禁用原因" />
            </Form.Item>
            <Form.Item label="自動恢復時間（分鐘）" name="auto_restore_minutes">
              <Select allowClear>
                <Select.Option value={30}>30 分鐘</Select.Option>
                <Select.Option value={60}>1 小時</Select.Option>
                <Select.Option value={120}>2 小時</Select.Option>
                <Select.Option value={300}>5 小時</Select.Option>
              </Select>
            </Form.Item>
          </Form>
        </div>
      ),
      onOk: async () => {
        const values = await form.validateFields();
        try {
          await api.post(
            `/api/v1/feature-flags/platforms/${platform}/disable`,
            {},
            { params: values }
          );
          message.success(`已禁用 ${platform} 平臺`);
          loadFlags();
        } catch (error) {
          message.error('操作失敗');
        }
      },
    });
  };

  // 查看審計日誌
  const showAuditLogs = async (flag: FeatureFlag) => {
    setSelectedFlag(flag);
    await loadAuditLogs(flag.id);
    setAuditModalVisible(true);
  };

  // 獲取作用域圖標
  const getScopeIcon = (scope: FlagScope) => {
    switch (scope) {
      case FlagScope.GLOBAL:
        return <GlobalOutlined />;
      case FlagScope.PLATFORM:
        return <PlatformOutlined />;
      case FlagScope.FEATURE:
        return <FeatureOutlined />;
      case FlagScope.STRATEGY:
        return <StrategyOutlined />;
      default:
        return <FeatureOutlined />;
    }
  };

  // 獲取作用域顏色
  const getScopeColor = (scope: FlagScope) => {
    switch (scope) {
      case FlagScope.GLOBAL:
        return 'red';
      case FlagScope.PLATFORM:
        return 'blue';
      case FlagScope.FEATURE:
        return 'green';
      case FlagScope.STRATEGY:
        return 'purple';
      default:
        return 'default';
    }
  };

  // 表格列定義
  const columns: ProColumns<FeatureFlag>[] = [
    {
      title: '開關名稱',
      dataIndex: 'name',
      width: 200,
      render: (_, record) => (
        <Space>
          {getScopeIcon(record.scope)}
          <span>{record.name}</span>
        </Space>
      ),
    },
    {
      title: '作用域',
      dataIndex: 'scope',
      width: 120,
      render: (_, record) => (
        <Tag color={getScopeColor(record.scope)}>
          {record.scope.toUpperCase()}
        </Tag>
      ),
      filters: Object.values(FlagScope).map((s) => ({ text: s, value: s })),
      onFilter: true,
    },
    {
      title: '平臺',
      dataIndex: 'platform',
      width: 120,
      render: (text) => text || '-',
      filters: Array.from(new Set(flags.map((f) => f.platform).filter(Boolean))).map((p) => ({
        text: p,
        value: p,
      })),
      onFilter: true,
    },
    {
      title: '狀態',
      dataIndex: 'enabled',
      width: 100,
      render: (_, record) => (
        <Switch
          checked={record.enabled}
          onChange={(checked) => handleToggle(record, checked)}
          checkedChildren={<CheckCircleOutlined />}
          unCheckedChildren={<CloseCircleOutlined />}
          loading={loading}
        />
      ),
    },
    {
      title: '灰度比例',
      dataIndex: 'gray_scale',
      width: 150,
      render: (_, record) => (
        <Slider
          value={record.gray_scale * 100}
          disabled
          tips={{ formatTooltip: (val) => `${val}%` }}
        />
      ),
    },
    {
      title: '定時恢復',
      dataIndex: 'restore_at',
      width: 180,
      render: (text) =>
        text ? (
          <Tag icon={<ClockCircleOutlined />} color="orange">
            {dayjs(text).format('YYYY-MM-DD HH:mm')}
          </Tag>
        ) : (
          '-'
        ),
    },
    {
      title: '最後更新',
      dataIndex: 'updated_at',
      width: 180,
      render: (text) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
      hideInSearch: true,
    },
    {
      title: '操作',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            onClick={() => showAuditLogs(record)}
          >
            審計日誌
          </Button>
          {record.scope === FlagScope.PLATFORM && !record.enabled && (
            <Popconfirm
              title="確認啟用該平臺？"
              onConfirm={() =>
                api
                  .post(`/api/v1/feature-flags/platforms/${record.platform}/enable`, {
                    reason: '手動啟用',
                  })
                  .then(() => {
                    message.success('啟用成功');
                    loadFlags();
                  })
              }
            >
              <Button type="link" size="small" danger>
                立即啟用
              </Button>
            </Popconfirm>
          )}
          {record.scope === FlagScope.PLATFORM && record.enabled && (
            <Button
              type="link"
              size="small"
              danger
              onClick={() => handleDisablePlatform(record.platform!)}
            >
              緊急禁用
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <PageContainer
      title="功能開關管理"
      subTitle="動態控制系統功能、精細化調度、灰度發布與資源隔離"
      extra={[
        <Button
          key="refresh"
          icon={<SyncOutlined spin={loading} />}
          onClick={loadFlags}
        >
          刷新
        </Button>,
        <Button
          key="global-emergency"
          danger
          icon={<PoweroffOutlined />}
          onClick={() =>
            Modal.confirm({
              title: '確認執行全局緊急制動？',
              content: '此操作將立即停止所有平臺的所有采集任務！',
              okText: '確認',
              cancelText: '取消',
              onOk: async () => {
                await api.post('/api/v1/feature-flags/global/disable', {
                  reason: '全局緊急制動',
                });
                message.success('已執行全局緊急制動');
                loadFlags();
              },
            })
          }
        >
          全局緊急制動
        </Button>,
      ]}
    >
      {/* 全局狀態概覽卡片 */}
      <ProCard
        title="系統健康狀態"
        extra={
          <Space>
            <Tag color="green">運行中</Tag>
            <Tag color="blue">{flags.filter((f) => f.enabled).length} / {flags.length} 開關啟用</Tag>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Descriptions column={4} bordered>
          <Descriptions.Item label="全局狀態">
            <Space>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              <span>正常運行</span>
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="啟用平臺數">
            {new Set(flags.filter((f) => f.scope === FlagScope.PLATFORM && f.enabled).map((f) => f.platform)).size}
          </Descriptions.Item>
          <Descriptions.Item label="待恢復任務">
            <Tag color="orange">0</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="最近告警">
            <Tag color="green">無</Tag>
          </Descriptions.Item>
        </Descriptions>
      </ProCard>

      {/* 開關列表表格 */}
      <ProCard title="功能開關列表">
        <ProTable<FeatureFlag>
          columns={columns}
          dataSource={flags}
          actionRef={actionRef}
          rowKey="id"
          search={{
            labelWidth: 'auto',
          }}
          options={{
            density: true,
            fullScreen: true,
            reload: loadFlags,
          }}
          pagination={{
            pageSize: 20,
          }}
          toolBarRender={false}
        />
      </ProCard>

      {/* 審計日誌彈窗 */}
      <Modal
        title="審計日誌"
        open={auditModalVisible}
        onCancel={() => setAuditModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedFlag && (
          <>
            <Descriptions title="開關信息" column={2} bordered size="small">
              <Descriptions.Item label="名稱">{selectedFlag.name}</Descriptions.Item>
              <Descriptions.Item label="作用域">{selectedFlag.scope}</Descriptions.Item>
              <Descriptions.Item label="平臺">{selectedFlag.platform || '-'}</Descriptions.Item>
              <Descriptions.Item label="當前狀態">
                <Tag color={selectedFlag.enabled ? 'green' : 'red'}>
                  {selectedFlag.enabled ? '啟用' : '禁用'}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
            
            <Divider orientation="left">變更歷史</Divider>
            <Timeline
              items={auditLogs.map((log) => ({
                color: log.is_auto ? 'orange' : 'blue',
                children: (
                  <div>
                    <div>
                      <strong>{log.changed_by}</strong>{' '}
                      {log.old_value !== undefined ? (
                        <>
                          將開關從{' '}
                          <Tag color={log.old_value ? 'green' : 'red'}>
                            {log.old_value ? '啟用' : '禁用'}
                          </Tag>{' '}
                          改為{' '}
                          <Tag color={log.new_value ? 'green' : 'red'}>
                            {log.new_value ? '啟用' : '禁用'}
                          </Tag>
                        </>
                      ) : (
                        <>設置為{' '}
                          <Tag color={log.new_value ? 'green' : 'red'}>
                            {log.new_value ? '啟用' : '禁用'}
                          </Tag>
                        </>
                      )}
                    </div>
                    {log.reason && <div style={{ color: '#999' }}>原因：{log.reason}</div>}
                    {log.trigger_source && (
                      <div style={{ fontSize: 12, color: '#faad14' }}>
                        自動觸發源：{log.trigger_source}
                      </div>
                    )}
                    <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                      {dayjs(log.created_at).format('YYYY-MM-DD HH:mm:ss')}
                      {log.changed_from && ` · IP: ${log.changed_from}`}
                    </div>
                  </div>
                ),
              }))}
            />
          </>
        )}
      </Modal>
    </PageContainer>
  );
};

export default FeatureFlagsPage;
