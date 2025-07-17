import axios from 'axios';

export const getStatistics = async () => {
  const res = await axios.get('/statistics');
  return res.data;
};

export const getRedisInfo = async () => {
  const res = await axios.get('/redis/info');
  return res.data;
};
