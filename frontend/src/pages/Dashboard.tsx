/**
 * 仪表板页面
 * 
 * 功能：
 * - 系统概览卡片（排队任务、运行中、今日任务、成功率）
 * - 各平台任务分布
 * - 实时任务状态
 * - 快捷操作入口
 */

import React, { useState, useEffect } from 'react';
import {
  PageContainer,
  ProCard,
  StatisticCard,
  ProTable,
} from '@ant-design/pro-components';
import {
  Row,
  Col,
  Tag,
  Space,
  Button,
  Progress,
  Spin,
  message,
} from 'antd';
import {
  SyncOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  RocketOutlined,
  WarningOutlined,
  PauseCircleOutlined,
} from '@ant-design/icons';
import { api } from '@/services/api';
import dayjs from 'dayjs';

const { Statistic } = StatisticCard;

interface DashboardStats {
  status_counts: Record<string, number>;
  queue_count: number;
  running_count: number;
  today_total: number;
  today_success: number;
  today_success_rate: number;
  today_items_collected: number;
  avg_duration_seconds: number;
  platform_counts: Record<string, number>;
  running_by_platform: Record<string, number>;
}

const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);

  const loadStats = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/v1/dashboard/stats');
      setStats(res);
    } catch (error) {
      message.error('加载仪表板数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    // 30 秒自动刷新
    const timer = setInterval(loadStats, 30000);
    return () => clearInterval(timer);
  }, []);

  if (!stats) {
    return (
      <PageContainer title="仪表板">
        <div style={{ textAlign: 'center', padding: 100 }}>
          <Spin size="large" tip="加载中..." />
        </div>
      </PageContainer>
    );
  }

  // 平台列表
  const platformEntries = Object.entries(stats.platform_counts).sort(
    (a, b) => b[1] - a[1]
  );

  return (
    <PageContainer
      title="仪表板"
      subTitle="系统运行概览"
      extra={[
        <Button
          key="refresh"
          icon={<SyncOutlined spin={loading} />}
          onClick={loadStats}
        >
          刷新
        </Button>,
      ]}
    >
      {/* ── 核心指标卡片 ──────────────────────────────── */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <ProCard hoverable>
            <Statistic
              title="排队中任务"
              value={stats.queue_count}
              icon={
                <ClockCircleOutlined
                  style={{ color: '#faad14', fontSize: 24 }}
                />
              }
              description={
                stats.queue_count > 50 ? (
                  <Tag color="warning">队列积压</Tag>
                ) : (
                  <Tag color="success">正常</Tag>
                )
              }
            />
          </ProCard>
        </Col>
        <Col span={6}>
          <ProCard hoverable>
            <Statistic
              title="运行中任务"
              value={stats.running_count}
              icon={
                <ThunderboltOutlined
                  style={{ color: '#1677ff', fontSize: 24 }}
                />
              }
              description={
                <Tag color="processing">实时</Tag>
              }
            />
          </ProCard>
        </Col>
        <Col span={6}>
          <ProCard hoverable>
            <Statistic
              title="今日任务总数"
              value={stats.today_total}
              icon={
                <BarChartOutlined
                  style={{ color: '#52c41a', fontSize: 24 }}
                />
              }
              description={
                <>
                  成功{' '}
                  <span style={{ color: '#52c41a' }}>
                    {stats.today_success}
                  </span>
                </>
              }
            />
          </ProCard>
        </Col>
        <Col span={6}>
          <ProCard hoverable>
            <Statistic
              title="今日成功率"
              value={stats.today_success_rate}
              suffix="%"
              icon={
                <CheckCircleOutlined
                  style={{
                    color:
                      stats.today_success_rate >= 90
                        ? '#52c41a'
                        : stats.today_success_rate >= 70
                        ? '#faad14'
                        : '#ff4d4f',
                    fontSize: 24,
                  }}
                />
              }
              description={
                <Progress
                  percent={stats.today_success_rate}
                  size="small"
                  showInfo={false}
                  strokeColor={
                    stats.today_success_rate >= 90
                      ? '#52c41a'
                      : stats.today_success_rate >= 70
                      ? '#faad14'
                      : '#ff4d4f'
                  }
                />
              }
            />
          </ProCard>
        </Col>
      </Row>

      {/* ── 二级指标 ──────────────────────────────────── */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <ProCard hoverable>
            <Statistic
              title="今日采集数据量"
              value={stats.today_items_collected}
              suffix="条"
              icon={
                <RocketOutlined
                  style={{ color: '#722ed1', fontSize: 24 }}
                />
              }
            />
          </ProCard>
        </Col>
        <Col span={8}>
          <ProCard hoverable>
            <Statistic
              title="平均任务耗时"
              value={stats.avg_duration_seconds}
              suffix="秒"
              precision={1}
              icon={
                <ClockCircleOutlined
                  style={{ color: '#13c2c2', fontSize: 24 }}
                />
              }
            />
          </ProCard>
        </Col>
        <Col span={8}>
          <ProCard hoverable>
            <Statistic
              title="任务状态分布"
              value={
                Object.values(stats.status_counts).reduce(
                  (a, b) => a + b,
                  0
                )
              }
              suffix="总任务"
              description={
                <Space size="small" wrap>
                  {Object.entries(stats.status_counts)
                    .filter(([, v]) => v > 0)
                    .map(([status, count]) => {
                      const colorMap: Record<string, string> = {
                        pending: 'default',
                        queued: 'processing',
                        running: 'processing',
                        success: 'success',
                        failed: 'error',
                        cancelled: 'warning',
                        retrying: 'warning',
                        timeout: 'error',
                      };
                      return (
                        <Tag
                          key={status}
                          color={colorMap[status] || 'default'}
                        >
                          {status}: {count}
                        </Tag>
                      );
                    })}
                </Space>
              }
            />
          </ProCard>
        </Col>
      </Row>

      {/* ── 平台分布 ──────────────────────────────────── */}
      <Row gutter={16}>
        <Col span={16}>
          <ProCard title="各平台任务分布" style={{ marginBottom: 24 }}>
            {platformEntries.length > 0 ? (
              <div>
                {platformEntries.map(([platform, count]) => {
                  const total = platformEntries.reduce(
                    (s, [, c]) => s + c,
                    0
                  );
                  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                  const running = stats.running_by_platform[platform] || 0;
                  const colorMap: Record<string, string> = {
                    bilibili: '#00a1d6',
                    douyin: '#000000',
                    weibo: '#ff8200',
                    instagram: '#e1306c',
                    telegram: '#0088cc',
                  };
                  return (
                    <div
                      key={platform}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        marginBottom: 16,
                      }}
                    >
                      <div style={{ width: 100, fontWeight: 500 }}>
                        <Tag color={colorMap[platform] || 'blue'}>
                          {platform}
                        </Tag>
                      </div>
                      <div style={{ flex: 1, marginRight: 16 }}>
                        <Progress
                          percent={pct}
                          strokeColor={colorMap[platform] || '#1677ff'}
                          size="small"
                        />
                      </div>
                      <div style={{ width: 120, textAlign: 'right' }}>
                        <span>{count} 个任务</span>
                        {running > 0 && (
                          <Tag color="processing" style={{ marginLeft: 8 }}>
                            {running} 运行中
                          </Tag>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div
                style={{
                  textAlign: 'center',
                  padding: 40,
                  color: '#999',
                }}
              >
                暂无任务数据
              </div>
            )}
          </ProCard>
        </Col>

        <Col span={8}>
          {/* ── 系统状态 ──────────────────────────────── */}
          <ProCard title="系统状态" style={{ marginBottom: 24 }}>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                <span>后端服务</span>
                <Tag color="success">运行中</Tag>
              </Space>
            </div>
            <div style={{ marginBottom: 16 }}>
              <Space>
                {stats.running_count > 0 ? (
                  <ThunderboltOutlined style={{ color: '#1677ff' }} />
                ) : (
                  <PauseCircleOutlined style={{ color: '#999' }} />
                )}
                <span>任务引擎</span>
                <Tag
                  color={stats.running_count > 0 ? 'processing' : 'default'}
                >
                  {stats.running_count > 0 ? '活跃' : '空闲'}
                </Tag>
              </Space>
            </div>
            <div style={{ marginBottom: 16 }}>
              <Space>
                {stats.queue_count > 50 ? (
                  <WarningOutlined style={{ color: '#faad14' }} />
                ) : (
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                )}
                <span>任务队列</span>
                <Tag
                  color={stats.queue_count > 50 ? 'warning' : 'success'}
                >
                  {stats.queue_count > 50 ? '积压' : '正常'}
                </Tag>
              </Space>
            </div>
          </ProCard>

          {/* ── 快捷操作 ──────────────────────────────── */}
          <ProCard title="快捷操作">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                type="primary"
                block
                icon={<RocketOutlined />}
                href="/tasks"
              >
                管理任务
              </Button>
              <Button
                block
                icon={<BarChartOutlined />}
                href="/tasks?tab=history"
              >
                查看历史
              </Button>
              <Button
                block
                icon={<ThunderboltOutlined />}
                href="/feature-flags"
              >
                功能开关
              </Button>
            </Space>
          </ProCard>
        </Col>
      </Row>
    </PageContainer>
  );
};

export default DashboardPage;
