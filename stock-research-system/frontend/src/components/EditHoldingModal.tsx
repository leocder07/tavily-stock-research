import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, InputNumber, DatePicker, Button, message, Popconfirm } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';
import { theme } from '../styles/theme';

interface EditHoldingModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  userEmail: string;
  holding: any;
}

const EditHoldingModal: React.FC<EditHoldingModalProps> = ({
  visible,
  onCancel,
  onSuccess,
  userEmail,
  holding
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    if (holding && visible) {
      form.setFieldsValue({
        shares: holding.shares,
        purchase_price: holding.purchase_price,
        purchase_date: holding.purchase_date ? dayjs(holding.purchase_date) : null,
        notes: holding.notes || ''
      });
    }
  }, [holding, visible, form]);

  const handleUpdate = async (values: any) => {
    setLoading(true);
    try {
      const payload: any = {};

      if (values.shares) payload.shares = values.shares;
      if (values.purchase_price) payload.purchase_price = values.purchase_price;
      if (values.purchase_date) payload.purchase_date = values.purchase_date.format('YYYY-MM-DD');
      if (values.notes !== undefined) payload.notes = values.notes;

      const response = await axios.put(
        `http://localhost:8000/api/v1/portfolio/${userEmail}/holdings/${holding.symbol}`,
        payload
      );

      if (response.data.status === 'success') {
        message.success(response.data.message);
        onSuccess();
      }
    } catch (error: any) {
      console.error('Error updating holding:', error);
      message.error(error.response?.data?.detail || 'Failed to update holding');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    setDeleteLoading(true);
    try {
      const response = await axios.delete(
        `http://localhost:8000/api/v1/portfolio/${userEmail}/holdings/${holding.symbol}`
      );

      if (response.data.status === 'success') {
        message.success(response.data.message);
        onSuccess();
      }
    } catch (error: any) {
      console.error('Error deleting holding:', error);
      message.error(error.response?.data?.detail || 'Failed to delete holding');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <Modal
      title={`Edit ${holding?.symbol} Holding`}
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={500}
      styles={{
        mask: { backgroundColor: 'rgba(0, 0, 0, 0.7)' }
      }}
    >
      <div style={{ backgroundColor: theme.colors.background.elevated, padding: '24px', borderRadius: 8 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpdate}
          requiredMark={false}
        >
          <Form.Item
            label={<span style={{ color: theme.colors.text.primary }}>Number of Shares</span>}
            name="shares"
          >
            <InputNumber
              min={0.01}
              step={1}
              style={{
                width: '100%',
                backgroundColor: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text.primary
              }}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ color: theme.colors.text.primary }}>Purchase Price per Share</span>}
            name="purchase_price"
          >
            <InputNumber
              min={0.01}
              step={0.01}
              precision={2}
              prefix="$"
              style={{
                width: '100%',
                backgroundColor: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text.primary
              }}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ color: theme.colors.text.primary }}>Purchase Date</span>}
            name="purchase_date"
          >
            <DatePicker
              style={{
                width: '100%',
                backgroundColor: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text.primary
              }}
              format="YYYY-MM-DD"
              disabledDate={(current) => current && current > dayjs().endOf('day')}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ color: theme.colors.text.primary }}>Notes</span>}
            name="notes"
          >
            <Input.TextArea
              rows={3}
              maxLength={200}
              style={{
                backgroundColor: theme.colors.background.elevated,
                border: `1px solid ${theme.colors.border}`,
                color: theme.colors.text.primary
              }}
            />
          </Form.Item>

          <div style={{ display: 'flex', gap: 12, justifyContent: 'space-between', marginTop: 24 }}>
            <Popconfirm
              title="Delete Holding"
              description={`Are you sure you want to remove ${holding?.symbol} from your portfolio?`}
              onConfirm={handleDelete}
              okText="Delete"
              cancelText="Cancel"
              okButtonProps={{ danger: true }}
            >
              <Button
                danger
                loading={deleteLoading}
                icon={<DeleteOutlined />}
                style={{
                  backgroundColor: theme.colors.background.elevated,
                  border: `1px solid ${theme.colors.danger}`,
                  color: theme.colors.danger
                }}
              >
                Delete
              </Button>
            </Popconfirm>

            <div style={{ display: 'flex', gap: 12 }}>
              <Button
                onClick={onCancel}
                style={{
                  backgroundColor: theme.colors.background.elevated,
                  border: `1px solid ${theme.colors.border}`,
                  color: theme.colors.text.secondary
                }}
              >
                Cancel
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                style={{
                  background: theme.colors.gradient.primary,
                  border: 'none',
                  color: '#000',
                  fontWeight: 600
                }}
              >
                Update
              </Button>
            </div>
          </div>
        </Form>
      </div>
    </Modal>
  );
};

export default EditHoldingModal;
