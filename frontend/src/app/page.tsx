"use client";
import React, { useState, useEffect, useRef } from "react";
import {
  Layout,
  Row,
  Col,
  Typography,
  Space,
  Upload,
  Button,
  List,
  Card,
  Input,
  InputNumber,
  Popconfirm,
  Divider,
  App,
  Empty,
  Tag,
  Modal,
  Drawer,
  Descriptions,
} from "antd";
import { InboxOutlined, SendOutlined, DeleteOutlined, ReloadOutlined, UploadOutlined, PlayCircleOutlined } from "@ant-design/icons";

const { Title, Text, Paragraph } = Typography;
const { Content, Sider } = Layout;

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type ResumeListItem = { id: number; filename: string; name: string; created_at: string };
type ScreeningItem = {
  id: number;
  filename: string;
  score: number;
  explain: Record<string, number>;
  score2: number;
  explain2: Record<string, number>;
  metadata: any;
};
type ChatMessage = { role: "user" | "assistant"; content: string };
type ResumeDetailResponse = { id: number; filename: string; created_at: string; meta: any };

export default function Home() {
  const { message } = App.useApp();
  // Resume List
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [resumeModalOpen, setResumeModalOpen] = useState(false);
  const [selectedResume, setSelectedResume] = useState<ResumeListItem | null>(null);
  const [resumeDetail, setResumeDetail] = useState<ResumeDetailResponse | null>(null);
  const [resumeDetailLoading, setResumeDetailLoading] = useState(false);

  // Resume Parse (upload)
  const [file, setFile] = useState<File | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [parseLoading, setParseLoading] = useState(false);

  // Screening
  const [jdText, setJdText] = useState("");
  const [topK, setTopK] = useState(10);
  const [screenLoading, setScreenLoading] = useState(false);
  const [screenResults, setScreenResults] = useState<ScreeningItem[]>([]);
  const [screenError, setScreenError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedScreenItem, setSelectedScreenItem] = useState<ScreeningItem | null>(null);
  const [screenDetail, setScreenDetail] = useState<ResumeDetailResponse | null>(null);
  const [screenDetailLoading, setScreenDetailLoading] = useState(false);

  // Chat
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchResumeList();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchResumeList = async () => {
    setListLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/resume/list`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResumes(data?.results || []);
    } catch (e: any) {
      message.error("获取简历列表失败");
    } finally {
      setListLoading(false);
    }
  };

  const onUpload = async () => {
    const target = file ?? files[0];
    if (!target) return;
    setParseLoading(true);
    try {
      const form = new FormData();
      form.append("file", target);
      const res = await fetch(`${API_BASE}/api/resume/parse`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      await res.json();
      setFile(null);
      setFiles([]);
      fetchResumeList();
      message.success("上传并解析成功");
    } catch (e: any) {
      message.error(e?.message || "上传解析失败");
    } finally {
      setParseLoading(false);
    }
  };

  const onUploadBatch = async () => {
    if (!files.length) return;
    setParseLoading(true);
    try {
      const form = new FormData();
      for (const f of files) form.append("files", f);
      const res = await fetch(`${API_BASE}/api/resume/parse/batch`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      await res.json();
      setFiles([]);
      setFile(null);
      fetchResumeList();
      message.success("批量上传并解析完成");
    } catch (e: any) {
      message.error(e?.message || "批量上传解析失败");
    } finally {
      setParseLoading(false);
    }
  };

  const onDelete = async (id: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/resume/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(await res.text());
      fetchResumeList();
      message.success("删除成功");
    } catch (e: any) {
      message.error("删除失败: " + e?.message);
    }
  };

  const onScreen = async () => {
    setScreenLoading(true);
    setScreenError(null);
    setScreenResults([]);
    try {
      const res = await fetch(`${API_BASE}/api/screening/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jd_text: jdText, top_k: topK }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setScreenResults(data?.results || []);
    } catch (e: any) {
      setScreenError(e?.message || "筛选失败");
      message.error(e?.message || "筛选失败");
    } finally {
      setScreenLoading(false);
    }
  };

  const onSendChat = async () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setChatLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [...messages, userMsg] }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      const assistantMsg: ChatMessage = { role: "assistant", content: data.reply };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: any) {
      const errorMsg: ChatMessage = { role: "assistant", content: `错误: ${e?.message}` };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Content style={{ padding: 24 }}>
        <div className="blur-aura" style={{ marginBottom: 16 }}>
          <Title level={3} className="gradient-title" style={{ marginBottom: 8 }}>智能简历筛选系统</Title>
          <Text type="secondary">上传、列表、JD筛选</Text>
        </div>
        <Row gutter={16}>
          {/* 左侧 */}
          <Col xs={24} md={12}>
            <Space direction="vertical" size="large" style={{ width: "100%" }}>
              {/* 上传 */}
              <Card
                className="glass-card glass-hover"
                hoverable
                title="上传简历 (PDF)"
                extra={
                  <Space>
                    <Button type="default" icon={<UploadOutlined />} disabled={!(file || files.length) || parseLoading} loading={parseLoading} onClick={onUpload}>上传并解析</Button>
                    <Button type="primary" icon={<UploadOutlined />} disabled={files.length === 0 || parseLoading} loading={parseLoading} onClick={onUploadBatch}>批量上传并解析</Button>
                  </Space>
                }
              >
                <Upload.Dragger
                  multiple={true}
                  accept="application/pdf"
                  beforeUpload={(f) => {
                    const real = f as File;
                    setFile(real); // 保持单文件上传可用（取第一个）
                    setFiles((prev) => [...prev, real]);
                    message.success(`${f.name} 已选择`);
                    return false; // 手动上传
                  }}
                  maxCount={20}
                  showUploadList={{ showRemoveIcon: true }}
                  onRemove={(info) => {
                    const name = (info as any)?.name as string;
                    setFiles((prev) => prev.filter((x) => x.name !== name));
                    if (file && file.name === name) setFile(null);
                    return true;
                  }}
                >
                  <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                  <p className="ant-upload-text">点击或拖拽PDF至此上传</p>
                  <p className="ant-upload-hint">仅用于解析简历内容，不会外发</p>
                </Upload.Dragger>
              </Card>

              {/* 列表 */}
              <Card
                className="glass-card glass-hover"
                hoverable
                title={`简历列表 (${resumes.length})`}
                extra={<Button icon={<ReloadOutlined />} onClick={fetchResumeList} loading={listLoading}>刷新</Button>}
                styles={{ body: { padding: 0 } }}
              >
                <div style={{ height: 180, overflow: "auto", padding: 16 }}>
                {resumes.length === 0 ? (
                  <Empty description="暂无简历" />
                ) : (
                  <List
                    style={{ height: 300, overflowY: "auto", margin: 0 }}
                    dataSource={resumes}
                    renderItem={(item) => (
                      <List.Item
                        actions={[
                          <Popconfirm
                            title="确定删除该简历？"
                            okText="删除"
                            cancelText="取消"
                            okButtonProps={{ danger: true }}
                            onConfirm={(e) => {
                              // 防止冒泡到 List.Item 的 onClick
                              // @ts-ignore
                              e?.domEvent?.stopPropagation?.();
                              onDelete(item.id);
                            }}
                            onCancel={(e) => {
                              // @ts-ignore
                              e?.domEvent?.stopPropagation?.();
                            }}
                            key="del"
                          >
                            <Button type="text" danger icon={<DeleteOutlined />} onClick={(e) => e.stopPropagation()}>删除</Button>
                          </Popconfirm>,
                        ]}
                        style={{ cursor: "default" }}
                      >
                        <div
                          onClick={async () => {
                            setSelectedResume(item);
                            setResumeDetail(null);
                            setResumeDetailLoading(true);
                            try {
                              const res = await fetch(`${API_BASE}/api/resume/detail/${item.id}`);
                              if (!res.ok) throw new Error(await res.text());
                              const data: ResumeDetailResponse = await res.json();
                              setResumeDetail(data);
                            } catch (e: any) {
                              message.error(e?.message || "获取详情失败");
                            } finally {
                              setResumeModalOpen(true);
                              setResumeDetailLoading(false);
                            }
                          }}
                          style={{ cursor: "pointer", flex: 1 }}
                        >
                          <List.Item.Meta
                            title={<Space size={8}><Text strong>{item.name || "未知"}</Text><Tag>{item.id}</Tag></Space>}
                            description={<Text type="secondary">{item.filename}</Text>}
                          />
                        </div>
                      </List.Item>
                    )}
                  />
                )}
                </div>
              </Card>

              {/* 筛选 */}
              <Card className="glass-card glass-hover" hoverable title="JD 筛选（三阶段 + 六维度二次评分）" extra={<Button type="primary" icon={<PlayCircleOutlined />} onClick={onScreen} loading={screenLoading}>运行筛选</Button>}>
                <Space direction="vertical" size="small" style={{ width: "100%" }}>
                  <Input.TextArea rows={6} placeholder="粘贴 JD 文本..." value={jdText} onChange={(e) => setJdText(e.target.value)} />
                  <Space>
                    <Text>TopK:</Text>
                    <InputNumber min={1} max={100} value={topK} onChange={(v) => setTopK(Number(v || 10))} />
                  </Space>
                </Space>
                {screenError && <Paragraph type="danger" style={{ marginTop: 8 }}>{screenError}</Paragraph>}
                {screenResults?.length > 0 && (
                  <List
                    style={{ marginTop: 12, maxHeight: 420, overflow: "auto" }}
                    dataSource={screenResults}
                    renderItem={(r, idx) => (
                      <List.Item onClick={async () => {
                        setSelectedScreenItem(r);
                        setScreenDetail(null);
                        setScreenDetailLoading(true);
                        try {
                          const res = await fetch(`${API_BASE}/api/resume/detail/${r.id}`);
                          if (res.ok) {
                            const data: ResumeDetailResponse = await res.json();
                            setScreenDetail(data);
                          }
                        } finally {
                          setDrawerOpen(true);
                          setScreenDetailLoading(false);
                        }
                      }} style={{ cursor: "pointer" }}>
                        <List.Item.Meta
                          title={<Space><Text strong>{idx + 1}. {r.filename}</Text><Tag color="blue">{r.score2.toFixed(4)}</Tag></Space>}
                          description={<Text type="secondary">技能 {r.explain2?.skills?.toFixed(2)} | 行业 {r.explain2?.domain?.toFixed(2)} | 薪资 {r.explain2?.salary?.toFixed(2)} | 学历 {r.explain2?.education?.toFixed(2)} | 地点 {r.explain2?.location?.toFixed(2)} | 标签 {r.explain2?.tags?.toFixed(2)}</Text>}
                        />
                      </List.Item>
                    )}
                  />
                )}
              </Card>
            </Space>
          </Col>

          {/* 右侧 */}
          <Col xs={24} md={12}>
            <Card className="glass-card glass-hover" hoverable title="简历智能对话" styles={{ body: { padding: 0 } }}>
              <div style={{ height: "70vh", display: "flex", flexDirection: "column" }}>
                <div style={{ flex: 1, overflow: "auto", padding: 16 }}>
                  {messages.length === 0 ? (
                    <Empty description="开始对话，咨询简历筛选相关问题..." />
                  ) : (
                    <List
                      dataSource={messages}
                      renderItem={(msg, idx) => (
                        <List.Item style={{ justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
                          <div style={{
                            maxWidth: "70%",
                            padding: 12,
                            borderRadius: 8,
                            background: msg.role === "user" ? "#1677ff" : "#f5f5f5",
                            color: msg.role === "user" ? "#fff" : "#333",
                          }}>
                            {msg.content}
                          </div>
                        </List.Item>
                      )}
                    />
                  )}
                  <div ref={chatEndRef} />
                </div>
                <Divider style={{ margin: 0 }} />
                <div style={{ padding: 12 }}>
                  <Space.Compact style={{ width: "100%" }}>
                    <Input
                      placeholder="输入消息..."
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onPressEnter={onSendChat}
                    />
                    <Button type="primary" icon={<SendOutlined />} loading={chatLoading} onClick={onSendChat}>
                      发送
                    </Button>
                  </Space.Compact>
                </div>
              </div>
            </Card>
          </Col>
        </Row>
        {/* 简历详情 Modal */}
        <Modal
          title={selectedResume ? `简历：${selectedResume.name || "未知"}` : "简历"}
          open={resumeModalOpen}
          onCancel={() => setResumeModalOpen(false)}
          footer={<Button type="primary" onClick={() => setResumeModalOpen(false)}>关闭</Button>}
        >
          {resumeDetailLoading ? (
            <Empty description="加载中..." />
          ) : resumeDetail ? (
            <Space direction="vertical" size="middle" style={{ width: "100%" }}>
              <Descriptions bordered size="small" column={1}
                items={[
                  { key: 'name', label: '姓名', children: resumeDetail.meta?.name || '未知' },
                  { key: 'filename', label: '文件名', children: resumeDetail.filename },
                  { key: 'created', label: '创建时间', children: resumeDetail.created_at },
                  resumeDetail.meta?.phone ? { key: 'phone', label: '电话', children: resumeDetail.meta.phone } : null,
                  resumeDetail.meta?.email ? { key: 'email', label: '邮箱', children: resumeDetail.meta.email } : null,
                  resumeDetail.meta?.location ? { key: 'location', label: '地点', children: resumeDetail.meta.location } : null,
                  resumeDetail.meta?.education ? { key: 'education', label: '学历', children: resumeDetail.meta.education } : null,
                  resumeDetail.meta?.school ? { key: 'school', label: '院校', children: resumeDetail.meta.school } : null,
                  resumeDetail.meta?.degree ? { key: 'degree', label: '学位', children: resumeDetail.meta.degree } : null,
                ].filter(Boolean) as any}
              />

              {Array.isArray(resumeDetail.meta?.skills) && resumeDetail.meta.skills.length > 0 && (
                <Space size={8} wrap>
                  {resumeDetail.meta.skills.map((s: any, idx: number) => (
                    <Tag key={idx} color="blue">{String(s)}</Tag>
                  ))}
                </Space>
              )}

              {Array.isArray(resumeDetail.meta?.experiences) && resumeDetail.meta.experiences.length > 0 && (
                <div className="glass-card" style={{ padding: 12 }}>
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    {resumeDetail.meta.experiences.map((exp: any, idx: number) => (
                      <div key={idx}>
                        <Text strong>{exp?.company || exp?.org || '经历'}</Text>
                        {exp?.title && <Text type="secondary" style={{ marginLeft: 8 }}>{exp.title}</Text>}
                        {exp?.duration && <Text type="secondary" style={{ marginLeft: 8 }}>{exp.duration}</Text>}
                        {exp?.desc && (<div style={{ marginTop: 4 }}><Text>{exp.desc}</Text></div>)}
                      </div>
                    ))}
                  </Space>
                </div>
              )}
            </Space>
          ) : (
            <Empty />
          )}
        </Modal>

        {/* 筛选详情 Drawer */}
        <Drawer
          title={selectedScreenItem ? `候选：${selectedScreenItem.filename}` : "候选详情"}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          width={520}
        >
          {selectedScreenItem ? (
            screenDetailLoading ? (
              <Empty description="加载中..." />
            ) : (
              <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                <Space>
                  <Tag color="blue">总分 {selectedScreenItem.score2.toFixed(4)}</Tag>
                </Space>
                {(() => {
                  const meta: any = (screenDetail?.meta ?? selectedScreenItem.metadata) || {};
                  return (
                    <>
                      <Descriptions bordered size="small" column={1}
                        items={[
                          { key: 'name', label: '姓名', children: meta.name || '未知' },
                          meta.phone ? { key: 'phone', label: '电话', children: meta.phone } : null,
                          meta.email ? { key: 'email', label: '邮箱', children: meta.email } : null,
                          meta.education ? { key: 'education', label: '学历', children: meta.education } : null,
                          meta.work_years != null ? { key: 'years', label: '工作年限', children: String(meta.work_years) } : null,
                          meta.current_company ? { key: 'cur_comp', label: '当前公司', children: meta.current_company } : null,
                          meta.current_title ? { key: 'cur_title', label: '当前职位', children: meta.current_title } : null,
                          meta.expected_salary ? { key: 'salary', label: '期望薪资', children: meta.expected_salary } : null,
                          meta.expected_city ? { key: 'expect_city', label: '期望城市', children: meta.expected_city } : null,
                          meta.expected_position ? { key: 'expect_pos', label: '期望职位', children: meta.expected_position } : null,
                          meta.links?.github ? { key: 'gh', label: 'GitHub', children: <a href={meta.links.github} target="_blank" rel="noreferrer">{meta.links.github}</a> } : null,
                          meta.links?.portfolio ? { key: 'pf', label: '作品集', children: <a href={meta.links.portfolio} target="_blank" rel="noreferrer">{meta.links.portfolio}</a> } : null,
                          selectedScreenItem.explain2?.skills != null ? { key: 's1', label: '技能匹配', children: selectedScreenItem.explain2.skills.toFixed(2) } : null,
                          selectedScreenItem.explain2?.domain != null ? { key: 's2', label: '行业匹配', children: selectedScreenItem.explain2.domain.toFixed(2) } : null,
                          selectedScreenItem.explain2?.salary != null ? { key: 's3', label: '薪资匹配', children: selectedScreenItem.explain2.salary.toFixed(2) } : null,
                          selectedScreenItem.explain2?.education != null ? { key: 's4', label: '学历匹配', children: selectedScreenItem.explain2.education.toFixed(2) } : null,
                          selectedScreenItem.explain2?.location != null ? { key: 's5', label: '地点匹配', children: selectedScreenItem.explain2.location.toFixed(2) } : null,
                          selectedScreenItem.explain2?.tags != null ? { key: 's6', label: '标签匹配', children: selectedScreenItem.explain2.tags.toFixed(2) } : null,
                        ].filter(Boolean) as any}
                      />

                      {Array.isArray(meta.skills) && meta.skills.length > 0 && (
                        <Space size={8} wrap>
                          {meta.skills.map((s: any, idx: number) => (
                            <Tag key={idx} color="blue">{String(s)}</Tag>
                          ))}
                        </Space>
                      )}

                      {meta.summary && (
                        <div className="glass-card" style={{ padding: 12 }}>
                          <Text>{meta.summary}</Text>
                        </div>
                      )}

                      {Array.isArray(meta.experiences) && meta.experiences.length > 0 && (
                        <div className="glass-card" style={{ padding: 12 }}>
                          <Space direction="vertical" size={8} style={{ width: '100%' }}>
                            {meta.experiences.map((exp: any, idx: number) => (
                              <div key={idx}>
                                <Text strong>{exp?.company || exp?.org || '经历'}</Text>
                                {exp?.title && <Text type="secondary" style={{ marginLeft: 8 }}>{exp.title}</Text>}
                                {exp?.duration && <Text type="secondary" style={{ marginLeft: 8 }}>{exp.duration}</Text>}
                                {exp?.desc && (<div style={{ marginTop: 4 }}><Text>{exp.desc}</Text></div>)}
                              </div>
                            ))}
                          </Space>
                        </div>
                      )}

                      {/* 项目经历 */}
                      {(() => {
                        const projectList: any[] = (meta.projects || meta.project_experiences || meta.projects_detail || meta.projectsText || []).filter(Boolean);
                        return (
                          <div className="glass-card" style={{ padding: 12 }}>
                            <Text strong>项目经历：</Text>
                            {projectList.length === 0 ? (
                              <div style={{ marginTop: 8 }}><Empty description="暂无" /></div>
                            ) : (
                              <Space direction="vertical" size={8} style={{ width: '100%', marginTop: 8 }}>
                                {projectList.map((p: any, idx: number) => (
                                  <div key={idx}>
                                    <Text strong>{(typeof p === 'string') ? p : (p?.name || '项目')}</Text>
                                    {typeof p !== 'string' && (
                                      <>
                                        {p?.role && <Text type="secondary" style={{ marginLeft: 8 }}>{p.role}</Text>}
                                        {p?.duration && <Text type="secondary" style={{ marginLeft: 8 }}>{p.duration}</Text>}
                                        {Array.isArray(p?.tech) && p.tech.length > 0 && (
                                          <div style={{ marginTop: 4 }}>
                                            <Space size={6} wrap>
                                              {p.tech.map((t: any, i: number) => <Tag key={i}>{String(t)}</Tag>)}
                                            </Space>
                                          </div>
                                        )}
                                        {p?.desc && (<div style={{ marginTop: 4 }}><Text>{p.desc}</Text></div>)}
                                      </>
                                    )}
                                  </div>
                                ))}
                              </Space>
                            )}
                          </div>
                        );
                      })()}

                      {/* 实习经历 */}
                      {(() => {
                        const internList: any[] = (meta.internships || meta.intern_experiences || meta.internship_experiences || meta.practice || []).filter(Boolean);
                        return (
                          <div className="glass-card" style={{ padding: 12 }}>
                            <Text strong>实习经历：</Text>
                            {internList.length === 0 ? (
                              <div style={{ marginTop: 8 }}><Empty description="暂无" /></div>
                            ) : (
                              <Space direction="vertical" size={8} style={{ width: '100%', marginTop: 8 }}>
                                {internList.map((it: any, idx: number) => (
                                  <div key={idx}>
                                    <Text strong>{(typeof it === 'string') ? it : (it?.company || it?.org || '实习')}</Text>
                                    {typeof it !== 'string' && (
                                      <>
                                        {it?.title && <Text type="secondary" style={{ marginLeft: 8 }}>{it.title}</Text>}
                                        {it?.duration && <Text type="secondary" style={{ marginLeft: 8 }}>{it.duration}</Text>}
                                        {it?.desc && (<div style={{ marginTop: 4 }}><Text>{it.desc}</Text></div>)}
                                      </>
                                    )}
                                  </div>
                                ))}
                              </Space>
                            )}
                          </div>
                        );
                      })()}

                      {Array.isArray(meta.educations || meta.schools) && (meta.educations || meta.schools).length > 0 && (
                        <div className="glass-card" style={{ padding: 12 }}>
                          <Space direction="vertical" size={6} style={{ width: '100%' }}>
                            {(meta.educations || meta.schools).map((ed: any, idx: number) => (
                              <div key={idx}>
                                <Text strong>{ed?.school || ed?.university || '教育经历'}</Text>
                                {ed?.degree && <Text type="secondary" style={{ marginLeft: 8 }}>{ed.degree}</Text>}
                                {ed?.major && <Text type="secondary" style={{ marginLeft: 8 }}>{ed.major}</Text>}
                                {ed?.duration && <Text type="secondary" style={{ marginLeft: 8 }}>{ed.duration}</Text>}
                              </div>
                            ))}
                          </Space>
                        </div>
                      )}

                      {Array.isArray(meta.languages) && meta.languages.length > 0 && (
                        <Space size={8} wrap>
                          {meta.languages.map((l: any, idx: number) => (
                            <Tag key={idx} color="geekblue">{typeof l === 'string' ? l : `${l?.name || ''} ${l?.level || ''}`}</Tag>
                          ))}
                        </Space>
                      )}

                      {Array.isArray(meta.awards) && meta.awards.length > 0 && (
                        <div className="glass-card" style={{ padding: 12 }}>
                          <Space direction="vertical" size={6} style={{ width: '100%' }}>
                            {meta.awards.map((a: any, idx: number) => (
                              <div key={idx}><Text>• {typeof a === 'string' ? a : (a?.name || '')}</Text></div>
                            ))}
                          </Space>
                        </div>
                      )}

                      {Array.isArray(meta.publications) && meta.publications.length > 0 && (
                        <div className="glass-card" style={{ padding: 12 }}>
                          <Space direction="vertical" size={6} style={{ width: '100%' }}>
                            {meta.publications.map((p: any, idx: number) => (
                              <div key={idx}><Text>• {typeof p === 'string' ? p : (p?.title || '')}</Text></div>
                            ))}
                          </Space>
                        </div>
                      )}
                      {Array.isArray(meta.certifications) && meta.certifications.length > 0 && (
                        <Space size={8} wrap>
                          {meta.certifications.map((c: any, idx: number) => (
                            <Tag key={idx}>{String(c)}</Tag>
                          ))}
                        </Space>
                      )}
                    </>
                  );
                })()}
              </Space>
            )
          ) : (
            <Empty />
          )}
        </Drawer>
      </Content>
    </Layout>
  );
}
