package me.shouheng.shuma.dao.handler;

import me.shouheng.shuma.model.enums.TopicType;
import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;
import org.apache.ibatis.type.MappedTypes;

import java.sql.CallableStatement;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/**
 * TopicTypeTypeHandler
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @version 2020/02/08 04:53
 */
@MappedTypes(value = {TopicType.class})
public class TopicTypeTypeHandler extends BaseTypeHandler<TopicType> {

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, TopicType parameter, JdbcType jdbcType) throws SQLException {
        ps.setInt(i, parameter.id);
    }

    @Override
    public TopicType getNullableResult(ResultSet rs, String columnName) throws SQLException {
        try {
            int id = rs.getInt(columnName);
            return TopicType.getTypeById(id);
        } catch (Exception ex) {
            return TopicType.NORMAL;
        }
    }

    @Override
    public TopicType getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        if (rs.wasNull()) {
            return TopicType.NORMAL;
        } else {
            int id = rs.getInt(columnIndex);
            return TopicType.getTypeById(id);
        }
    }

    @Override
    public TopicType getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        if (cs.wasNull()) {
            return TopicType.NORMAL;
        } else {
            int id = cs.getInt(columnIndex);
            return TopicType.getTypeById(id);
        }
    }
}
