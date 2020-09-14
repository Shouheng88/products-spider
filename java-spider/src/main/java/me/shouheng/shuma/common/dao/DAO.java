package me.shouheng.shuma.common.dao;

import me.shouheng.shuma.common.exception.DAOException;
import me.shouheng.shuma.common.model.query.SearchObject;

import java.util.List;

/**
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019-08-01  20:30
 */
public interface DAO<T> {

    int insert(T entity) throws DAOException;

    int update(T entity) throws DAOException;

    int updatePOSelective(T entity) throws DAOException;

    List<T> searchBySo(SearchObject so) throws DAOException;

    long searchCountBySo(SearchObject so) throws DAOException;

    int deleteByPrimaryKey(Long id) throws DAOException;

    T selectByPrimaryKey(Long id) throws DAOException;
}
