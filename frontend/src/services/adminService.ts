import axios from 'axios';

export const cleanupOldData = async (days = 30) => {
  const res = await axios.post('/admin/cleanup', { days });
  return res.data;
};

export const exportConversations = async (format = 'json', days = 7) => {
  const res = await axios.get('/admin/export', { params: { format, days } });
  return res.data;
};
